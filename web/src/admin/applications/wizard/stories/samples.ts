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

export const dummyAuthenticationFlowsSearch = {
    pagination: {
        next: 0,
        previous: 0,
        count: 2,
        current: 1,
        total_pages: 1,
        start_index: 1,
        end_index: 2,
    },
    results: [
        {
            pk: "2594b1a0-f234-4965-8b93-a8631a55bd5c",
            policybindingmodel_ptr_id: "0bc529a6-dcd0-4ba8-8fef-5702348832f9",
            name: "Welcome to authentik!",
            slug: "default-authentication-flow",
            title: "Welcome to authentik!",
            designation: "authentication",
            background: "/static/dist/assets/images/flow_background.jpg",
            stages: [
                "bad9fbce-fb86-4ba4-8124-e7a1d8c147f3",
                "1da1f272-a76e-4112-be95-f02421fca1d4",
                "945cd956-6670-4dfa-ab3a-2a72dd3051a7",
                "0fc1fc5c-b928-4d99-a892-9ae48de089f5",
            ],
            policies: [],
            cache_count: 0,
            policy_engine_mode: "any",
            compatibility_mode: false,
            export_url: "/api/v3/flows/instances/default-authentication-flow/export/",
            layout: "stacked",
            denied_action: "message_continue",
            authentication: "none",
        },
        {
            pk: "3526dbd1-b50e-4553-bada-fbe7b3c2f660",
            policybindingmodel_ptr_id: "cde67954-b78a-4fe9-830e-c2aba07a724a",
            name: "Welcome to authentik!",
            slug: "default-source-authentication",
            title: "Welcome to authentik!",
            designation: "authentication",
            background: "/static/dist/assets/images/flow_background.jpg",
            stages: ["3713b252-cee3-4acb-a02f-083f26459fff"],
            policies: ["f42a4c7f-6586-4b14-9325-a832127ba295"],
            cache_count: 0,
            policy_engine_mode: "any",
            compatibility_mode: false,
            export_url: "/api/v3/flows/instances/default-source-authentication/export/",
            layout: "stacked",
            denied_action: "message_continue",
            authentication: "require_unauthenticated",
        },
    ],
};

export const dummyCoreGroupsSearch = {
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
            pk: "67543d37-0ee2-4a4c-b020-9e735a8b5178",
            num_pk: 13734,
            name: "authentik Admins",
            is_superuser: true,
            parent: null,
            users: [1],
            attributes: {},
            users_obj: [
                {
                    pk: 1,
                    username: "akadmin",
                    name: "authentik Default Admin",
                    is_active: true,
                    last_login: "2023-07-03T16:08:11.196942Z",
                    email: "ken@goauthentik.io",
                    attributes: {
                        settings: {
                            locale: "en",
                        },
                    },
                    uid: "6dedc98b3fdd0f9afdc705e9d577d61127d89f1d91ea2f90f0b9a353615fb8f2",
                },
            ],
        },
    ],
};

// prettier-ignore
export const dummyProviderTypesList = [
    ["LDAP Provider", "ldapprovider", 
     "Allow applications to authenticate against authentik's users using LDAP.", 
    ], 
    ["OAuth2/OpenID Provider", "oauth2provider", 
     "OAuth2 Provider for generic OAuth and OpenID Connect Applications.", 
    ], 
    ["Proxy Provider", "proxyprovider", 
     "Protect applications that don't support any of the other\n    Protocols by using a Reverse-Proxy.", 
    ], 
    ["Radius Provider", "radiusprovider", 
     "Allow applications to authenticate against authentik's users using Radius.", 
    ], 
    ["SAML Provider", "samlprovider", 
     "SAML 2.0 Endpoint for applications which support SAML.", 
    ], 
    ["SCIM Provider", "scimprovider", 
     "SCIM 2.0 provider to create users and groups in external applications", 
    ], 
    ["SAML Provider from Metadata", "", 
     "Create a SAML Provider by importing its Metadata.", 
    ], 
].map(([name, model_name, description]) => ({ name, description, model_name }));
