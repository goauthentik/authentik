use eyre::Result;
use rcgen::{
    Certificate, CertificateParams, DistinguishedName, DnType, ExtendedKeyUsagePurpose, KeyPair,
    KeyUsagePurpose, PKCS_RSA_SHA256, SanType,
};
use rustls::{
    crypto::aws_lc_rs::sign::any_supported_type,
    pki_types::{CertificateDer, PrivateKeyDer},
    sign::CertifiedKey,
};
use time::{Duration, OffsetDateTime};

pub fn generate() -> Result<(Certificate, KeyPair)> {
    let signing_key = KeyPair::generate_for(&PKCS_RSA_SHA256)?;

    let mut params = CertificateParams::default();
    params.not_before = OffsetDateTime::now_utc();
    params.not_after = OffsetDateTime::now_utc() + Duration::days(365);
    params.distinguished_name = {
        let mut dn = DistinguishedName::new();
        dn.push(DnType::OrganizationName, "authentik");
        dn.push(DnType::CommonName, "authentik default certificate");
        dn
    };
    params.subject_alt_names = vec![SanType::DnsName("*".try_into()?)];
    params.key_usages = vec![
        KeyUsagePurpose::DigitalSignature,
        KeyUsagePurpose::KeyEncipherment,
    ];
    params.extended_key_usages = vec![ExtendedKeyUsagePurpose::ServerAuth];

    let cert = params.self_signed(&signing_key)?;

    Ok((cert, signing_key))
}

pub fn generate_certifiedkey() -> Result<CertifiedKey> {
    let (cert, keypair) = generate()?;

    let cert_der = cert.der().to_vec();
    let key_der = keypair.serialize_der();

    let private_key =
        PrivateKeyDer::try_from(key_der).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;
    let signing_key =
        any_supported_type(&private_key).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;

    Ok(CertifiedKey::new(
        vec![CertificateDer::from(cert_der)],
        signing_key,
    ))
}
