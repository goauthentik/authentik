use std::{
    collections::{HashMap, hash_map::Entry},
    io::BufReader,
    sync::Arc,
};

use eyre::{Report, Result, eyre};
use rustls::{
    RootCertStore,
    crypto::CryptoProvider,
    pki_types::{CertificateDer, PrivateKeyDer},
    server::ClientHello,
    sign::CertifiedKey,
};
use rustls_pemfile::{certs, private_key};

use crate::db;

#[derive(Debug)]
struct Brand {
    domain: String,
    default: bool,
    web_certificate: Arc<CertifiedKey>,
}

#[derive(Debug)]
pub(crate) struct CertResolver {
    brands: Vec<Brand>,
}

impl CertResolver {
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

pub(crate) async fn make_cert_managers() -> Result<(CertResolver, RootCertStore)> {
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

        for row in rows {
            let BrandRow {
                brand_uuid,
                domain,
                default,
                web_cert_data,
                web_cert_key,
                client_cert_data,
            } = row;

            if let (Some(certificate_data), Some(key_data)) = (web_cert_data, web_cert_key)
                && let Entry::Vacant(e) = brands.entry(brand_uuid)
            {
                let brand = Brand {
                    domain,
                    default,
                    web_certificate: {
                        let cert_chain: Vec<CertificateDer<'static>> =
                            certs(&mut BufReader::new(certificate_data.as_bytes()))
                                .collect::<Result<Vec<_>, _>>()?;
                        let key_der: PrivateKeyDer<'static> =
                            private_key(&mut BufReader::new(key_data.as_bytes()))?
                                .ok_or(eyre!("no private key found"))?;
                        let provider =
                            CryptoProvider::get_default().expect("no rustls provider installed");
                        Arc::new(CertifiedKey::new(
                            cert_chain,
                            provider.key_provider.load_private_key(key_der)?,
                        ))
                    },
                };
                e.insert(brand);
            };

            if let Some(certificate_data) = client_cert_data {
                let cert_chain: Vec<CertificateDer<'static>> =
                    certs(&mut BufReader::new(certificate_data.as_bytes()))
                        .collect::<Result<Vec<_>, _>>()?;
                for cert in cert_chain {
                    roots.add(cert)?;
                }
            }
        }

        Ok::<_, Report>((brands, roots))
    })
    .await??;

    Ok((
        CertResolver {
            brands: brands.into_values().collect(),
        },
        roots,
    ))
}
