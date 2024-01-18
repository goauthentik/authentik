export const dummyCryptoCertsSearch = {
    pagination: {
        next: 0,
        previous: 0,
        count: 1,
        current: 1,
        total_pages: 1,
        start_index: 1,
        end_index: 1,
    },

    results: [
        {
            pk: "63efd1b8-6c39-4f65-8157-9a406cb37447",
            name: "authentik Self-signed Certificate",
            fingerprint_sha256: null,
            fingerprint_sha1: null,
            cert_expiry: null,
            cert_subject: null,
            private_key_available: true,
            private_key_type: null,
            certificate_download_url:
                "/api/v3/crypto/certificatekeypairs/63efd1b8-6c39-4f65-8157-9a406cb37447/view_certificate/?download",
            private_key_download_url:
                "/api/v3/crypto/certificatekeypairs/63efd1b8-6c39-4f65-8157-9a406cb37447/view_private_key/?download",
            managed: null,
        },
    ],
};
