import {
    dummyAuthenticationFlowsSearch,
    dummyAuthorizationFlowsSearch,
    dummyCoreGroupsSearch,
    dummyCryptoCertsSearch,
    dummyHasJwks,
    dummyPropertyMappings,
    dummyProviderTypesList,
    dummySAMLProviderMappings,
} from "./samples";

export const mockData = [
    {
        url: "/api/v3/providers/all/types/",
        method: "GET",
        status: 200,
        response: dummyProviderTypesList,
    },
    {
        url: "/api/v3/core/groups/?ordering=name",
        method: "GET",
        status: 200,
        response: dummyCoreGroupsSearch,
    },

    {
        url: "/api/v3/crypto/certificatekeypairs/?has_key=true&include_details=false&ordering=name",
        method: "GET",
        status: 200,
        response: dummyCryptoCertsSearch,
    },
    {
        url: "/api/v3/flows/instances/?designation=authentication&ordering=slug",
        method: "GET",
        status: 200,
        response: dummyAuthenticationFlowsSearch,
    },
    {
        url: "/api/v3/flows/instances/?designation=authorization&ordering=slug",
        method: "GET",
        status: 200,
        response: dummyAuthorizationFlowsSearch,
    },
    {
        url: "/api/v3/propertymappings/scope/?ordering=scope_name",
        method: "GET",
        status: 200,
        response: dummyPropertyMappings,
    },
    {
        url: "/api/v3/sources/oauth/?has_jwks=true&ordering=name",
        method: "GET",
        status: 200,
        response: dummyHasJwks,
    },
    {
        url: "/api/v3/propertymappings/saml/?ordering=saml_name",
        method: "GET",
        status: 200,
        response: dummySAMLProviderMappings,
    },
];
