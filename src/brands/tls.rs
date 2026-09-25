use std::{
    collections::{HashMap, HashSet, hash_map::Entry},
    sync::Arc,
};

use ak_common::db;
use eyre::{Report, Result};
use rustls::{
    RootCertStore,
    crypto::CryptoProvider,
    pki_types::{CertificateDer, PrivateKeyDer, pem::PemObject as _},
    server::ClientHello,
    sign::CertifiedKey,
};
use tracing::warn;

#[derive(Debug)]
struct Brand {
    domain: String,
    default: bool,
    web_certificate: Arc<CertifiedKey>,
}

#[derive(Debug)]
pub(crate) struct BrandCertResolver {
    brands: Vec<Brand>,
}

impl BrandCertResolver {
    pub(crate) fn resolve(&self, client_hello: &ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        let server_name = client_hello.server_name()?;
        let mut best = None;

        for brand in &self.brands {
            if best.is_none() && brand.default {
                best = Some(Arc::clone(&brand.web_certificate));
            }
            if server_name == brand.domain || server_name.ends_with(&format!(".{}", brand.domain)) {
                best = Some(Arc::clone(&brand.web_certificate));
            }
        }

        best
    }
}

/// Build a rustls [`CertifiedKey`] from a brand's PEM certificate chain and private key.
///
/// Returns an error (rather than propagating out of the reload) so a single unloadable
/// certificate can be skipped without affecting other brands.
fn certified_key(certificate_data: &str, key_data: &str) -> Result<Arc<CertifiedKey>> {
    let cert_chain = CertificateDer::pem_reader_iter(certificate_data.as_bytes())
        .collect::<Result<Vec<_>, _>>()?;
    let key_der = PrivateKeyDer::from_pem_reader(key_data.as_bytes())?;
    let provider = CryptoProvider::get_default().expect("no rustls provider installed");
    Ok(Arc::new(CertifiedKey::new(
        cert_chain,
        provider.key_provider.load_private_key(key_der)?,
    )))
}

pub(crate) async fn make_cert_managers() -> Result<(BrandCertResolver, RootCertStore)> {
    #[derive(sqlx::FromRow)]
    struct BrandRow {
        brand_uuid: uuid::Uuid,
        domain: String,
        default: bool,
        web_cert_data: Option<String>,
        web_cert_key: Option<String>,
        client_cert_data: Option<String>,
    }

    let rows = sqlx::query_as::<_, BrandRow>(
        "
            SELECT
                b.brand_uuid,
                b.domain,
                b.default,
                wc.certificate_data AS web_cert_data,
                wc.key_data AS web_cert_key,
                cc.certificate_data AS client_cert_data
            FROM authentik_brands_brand b
            LEFT JOIN authentik_crypto_certificatekeypair wc
                ON wc.kp_uuid = b.web_certificate_id
            LEFT JOIN authentik_brands_brand_client_certificates bcc
                ON bcc.brand_id = b.brand_uuid
            LEFT JOIN authentik_crypto_certificatekeypair cc
                ON cc.kp_uuid = bcc.certificatekeypair_id
        ",
    )
    .fetch_all(db::get())
    .await?;

    let (brands, roots) = tokio::task::spawn_blocking(|| {
        let mut brands = HashMap::new();
        let mut roots = RootCertStore::empty();
        // Brands whose web certificate we've already tried to load, so a brand that appears in
        // several rows (one per client-trust certificate) is only built and logged once.
        let mut web_attempted = HashSet::new();

        for row in rows {
            let BrandRow {
                brand_uuid,
                domain,
                default,
                web_cert_data,
                web_cert_key,
                client_cert_data,
            } = row;

            // Load each brand's web certificate independently. A certificate that fails to parse
            // or uses a key algorithm rustls can't load (e.g. Ed448) must only drop that one brand,
            // never abort the reload for every other brand.
            if let (Some(certificate_data), Some(key_data)) = (web_cert_data, web_cert_key)
                && web_attempted.insert(brand_uuid)
                && let Entry::Vacant(e) = brands.entry(brand_uuid)
            {
                match certified_key(&certificate_data, &key_data) {
                    Ok(web_certificate) => {
                        e.insert(Brand {
                            domain,
                            default,
                            web_certificate,
                        });
                    }
                    Err(err) => {
                        warn!(
                            %brand_uuid,
                            %domain,
                            ?err,
                            "skipping brand web certificate that failed to load"
                        );
                    }
                }
            }

            // Likewise, a client-trust certificate that fails to parse is skipped rather than
            // taking the whole trust store (and the reload) down with it.
            if let Some(certificate_data) = client_cert_data {
                match CertificateDer::pem_reader_iter(certificate_data.as_bytes())
                    .collect::<Result<Vec<_>, _>>()
                {
                    Ok(cert_chain) => {
                        for cert in cert_chain {
                            if let Err(err) = roots.add(cert) {
                                warn!(%brand_uuid, ?err, "skipping invalid client trust certificate");
                            }
                        }
                    }
                    Err(err) => {
                        warn!(%brand_uuid, ?err, "skipping unparseable client trust certificate");
                    }
                }
            }
        }

        Ok::<_, Report>((brands, roots))
    })
    .await??;

    Ok((
        BrandCertResolver {
            brands: brands.into_values().collect(),
        },
        roots,
    ))
}
