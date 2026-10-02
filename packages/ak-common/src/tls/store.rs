use std::{collections::HashMap, sync::Arc};

use ak_client::apis::{
    configuration::Configuration,
    crypto_api::{
        crypto_certificatekeypairs_retrieve, crypto_certificatekeypairs_view_certificate_retrieve,
        crypto_certificatekeypairs_view_private_key_retrieve,
    },
};
use eyre::{Report, Result};
use futures::FutureExt as _;
use rustls::{
    crypto::CryptoProvider,
    pki_types::{CertificateDer, PrivateKeyDer, pem::PemObject as _},
    sign::CertifiedKey,
};
use tokio::sync::Mutex;
use uuid::Uuid;

#[derive(Debug)]
pub struct Certificate {
    pub fingerprint: String,

    pub certificate: String,
    pub key: String,

    pub certified_key: Arc<CertifiedKey>,
}

#[derive(Clone, Debug, Default)]
pub struct CertificateStore {
    certificates: Arc<Mutex<HashMap<Uuid, Arc<Certificate>>>>,
}

impl CertificateStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub async fn ensure_keypair(
        &self,
        api_config: &Configuration,
        kp_uuid: Uuid,
    ) -> Result<Arc<Certificate>> {
        let kp_uuid_s = kp_uuid.to_string();

        let fingerprint = crypto_certificatekeypairs_retrieve(api_config, &kp_uuid_s)
            .await?
            .fingerprint_sha256;

        if let Some(certificate) = self.certificates.lock().await.get(&kp_uuid)
            && let Some(fingerprint) = &fingerprint
            && &certificate.fingerprint == fingerprint
        {
            return Ok(Arc::clone(certificate));
        }

        let (cert, key) = tokio::try_join!(
            crypto_certificatekeypairs_view_certificate_retrieve(api_config, &kp_uuid_s, None,)
                .map(|res| res.map_err(Report::from)),
            crypto_certificatekeypairs_view_private_key_retrieve(api_config, &kp_uuid_s, None,)
                .map(|res| res.map_err(Report::from)),
        )?;

        let certified_key = {
            let cert_chain = CertificateDer::pem_reader_iter(cert.data.as_bytes())
                .collect::<Result<Vec<_>, _>>()?;
            let key_der = PrivateKeyDer::from_pem_reader(key.data.as_bytes())?;
            let provider = CryptoProvider::get_default().expect("no rustls provider installed");
            Arc::new(CertifiedKey::new(
                cert_chain,
                provider.key_provider.load_private_key(key_der)?,
            ))
        };

        let cert = Arc::new(Certificate {
            fingerprint: fingerprint.unwrap_or_default(),
            certificate: cert.data,
            key: key.data,
            certified_key,
        });

        if !cert.fingerprint.is_empty() {
            self.certificates
                .lock()
                .await
                .insert(kp_uuid, Arc::clone(&cert));
        }

        Ok(cert)
    }
}
