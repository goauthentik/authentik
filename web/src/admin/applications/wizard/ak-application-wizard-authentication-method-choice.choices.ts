import { msg } from "@lit/localize";

import type { TypeCreate } from "@goauthentik/api";

type ProviderType = [string, string, string] | [string, string, string, ProviderType[]];

type ProviderOption = TypeCreate & {
    children?: TypeCreate[];
};

// prettier-ignore
const _providerTypesTable: ProviderType[] = [
    ["oauth2provider", msg("OAuth2/OpenID"), msg("Modern applications, APIs and Single-page applications.")],
    ["ldapprovider", msg("LDAP"), msg("Provide an LDAP interface for applications and users to authenticate against.")],
    ["proxyprovider-proxy", msg("Transparent Reverse Proxy"), msg("For transparent reverse proxies with required authentication")],
    ["proxyprovider-forwardsingle", msg("Forward Single Proxy"), msg("For nginx's auth_request or traefix's forwardAuth")],
    ["radiusprovider", msg("Radius"), msg("Allow applications to authenticate against authentik's users using Radius.")],
    ["samlprovider-manual", msg("SAML Manual configuration"), msg("Configure SAML provider manually")],
    ["samlprovider-import", msg("SAML Import Configuration"), msg("Create a SAML provider by importing its metadata")],
    ["scimprovider", msg("SCIM Provider"), msg("SCIM 2.0 provider to create users and groups in external applications")]
];

function mapProviders([modelName, name, description, children]: ProviderType): ProviderOption {
    return {
        modelName,
        name,
        description,
        component: "",
        ...(children ? { children: children.map(mapProviders) } : {}),
    };
}

export const providerTypesList = _providerTypesTable.map(mapProviders);

export default providerTypesList;
