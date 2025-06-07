import {
    type TestProvider,
    type TestSequence,
    checkIsPresent,
    clickButton,
    clickToggleGroup,
    setFormGroup,
    setRadio,
    setSearchSelect,
    setTextInput,
    setTextareaInput,
    setToggle,
    setTypeCreate,
} from "pageobjects/controls.js";

import { ascii_letters, digits, randomString } from "../utils";
import { randomId } from "../utils/index.js";

const newObjectName = (prefix: string) => `${prefix} - ${randomId()}`;

// components.schemas.OAuth2ProviderRequest
//
// - name
// - authentication_flow
// - authorization_flow
// - invalidation_flow
// - property_mappings
// - client_type
// - client_id
// - client_secret
// - access_code_validity
// - access_token_validity
// - refresh_token_validity
// - include_claims_in_id_token
// - signing_key
// - encryption_key
// - redirect_uris
// - sub_mode
// - issuer_mode
// - jwks_sources
//
export const simpleOAuth2ProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "OAuth2/OpenID Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Oauth2 Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
];

export const completeOAuth2ProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "OAuth2/OpenID Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Oauth2 Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [setFormGroup, /Protocol settings/, "open"],
    [setRadio, "clientType", "Public"],
    // Switch back so we can make sure `clientSecret` is available.
    [setRadio, "clientType", "Confidential"],
    [checkIsPresent, '[name="clientId"]'],
    [checkIsPresent, '[name="clientSecret"]'],
    [setSearchSelect, "signingKey", /authentik Self-signed Certificate/],
    [setSearchSelect, "encryptionKey", /authentik Self-signed Certificate/],
    [setFormGroup, /Advanced flow settings/, "open"],
    [setSearchSelect, "authenticationFlow", /default-source-authentication/],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [setFormGroup, /Advanced protocol settings/, "open"],
    [setTextInput, "accessCodeValidity", "minutes=2"],
    [setTextInput, "accessTokenValidity", "minutes=10"],
    [setTextInput, "refreshTokenValidity", "days=40"],
    [setToggle, "includeClaimsInIdToken", false],
    [checkIsPresent, '[name="redirectUris"]'],
    [setRadio, "subMode", "Based on the User's username"],
    [setRadio, "issuerMode", "Same identifier is used for all providers"],
    [setFormGroup, /Machine-to-Machine authentication settings/, "open"],
    [checkIsPresent, '[name="jwtFederationSources"]'],
    [checkIsPresent, '[name="jwtFederationProviders"]'],
];

// components.schemas.LDAPProviderRequest
//
// - name
// - authentication_flow
// - authorization_flow
// - invalidation_flow
// - base_dn
// - certificate
// - tls_server_name
// - uid_start_number
// - gid_start_number
// - search_mode
// - bind_mode
// - mfa_support
//
export const simpleLDAPProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "LDAP Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New LDAP Provider")],
    // This will never not weird me out.
    [setFormGroup, /Flow settings/, "open"],
    [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
];

export const completeLDAPProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "LDAP Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New LDAP Provider")],
    [setFormGroup, /Flow settings/, "open"],
    [setFormGroup, /Protocol settings/, "open"],
    [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [setTextInput, "baseDn", "DC=ldap-2,DC=goauthentik,DC=io"],
    [setSearchSelect, "certificate", /authentik Self-signed Certificate/],
    [checkIsPresent, '[name="tlsServerName"]'],
    [setTextInput, "uidStartNumber", "2001"],
    [setTextInput, "gidStartNumber", "4001"],
    [setRadio, "searchMode", "Direct querying"],
    [setRadio, "bindMode", "Direct binding"],
    [setToggle, "mfaSupport", false],
];

export const simpleRadiusProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Radius Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Radius Provider")],
    [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
];

export const completeRadiusProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Radius Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Radius Provider")],
    [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
    [setFormGroup, /Advanced flow settings/, "open"],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [setFormGroup, /Protocol settings/, "open"],
    [setToggle, "mfaSupport", false],
    [setTextInput, "clientNetworks", ""],
    [setTextInput, "clientNetworks", "0.0.0.0/0, ::/0"],
    [setTextInput, "sharedSecret", randomString(128, ascii_letters + digits)],
    [checkIsPresent, '[name="propertyMappings"]'],
];

// provider_components.schemas.SAMLProviderRequest.yml
//
// - name
// - authentication_flow
// - authorization_flow
// - invalidation_flow
// - property_mappings
// - acs_url
// - audience
// - issuer
// - assertion_valid_not_before
// - assertion_valid_not_on_or_after
// - session_valid_not_on_or_after
// - name_id_mapping
// - digest_algorithm
// - signature_algorithm
// - signing_kp
// - verification_kp
// - encryption_kp
// - sign_assertion
// - sign_response
// - sp_binding
// - default_relay_state
//
export const simpleSAMLProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "SAML Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SAML Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [setTextInput, "acsUrl", "http://example.com:8000/"],
];

export const completeSAMLProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "SAML Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SAML Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [setTextInput, "acsUrl", "http://example.com:8000/"],
    [setTextInput, "issuer", "someone-else"],
    [setRadio, "spBinding", "Post"],
    [setTextInput, "audience", ""],
    [setFormGroup, /Advanced flow settings/, "open"],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [setSearchSelect, "authenticationFlow", /default-source-authentication/],
    [setFormGroup, /Advanced protocol settings/, "open"],
    [checkIsPresent, '[name="propertyMappings"]'],
    [setSearchSelect, "signingKp", /authentik Self-signed Certificate/],
    [setSearchSelect, "verificationKp", /authentik Self-signed Certificate/],
    [setSearchSelect, "encryptionKp", /authentik Self-signed Certificate/],
    [setSearchSelect, "nameIdMapping", /authentik default SAML Mapping. Username/],
    [setTextInput, "assertionValidNotBefore", "minutes=-10"],
    [setTextInput, "assertionValidNotOnOrAfter", "minutes=10"],
    [setTextInput, "sessionValidNotOnOrAfter", "minutes=172800"],
    [checkIsPresent, '[name="defaultRelayState"]'],
    [setRadio, "digestAlgorithm", "SHA512"],
    [setRadio, "signatureAlgorithm", "RSA-SHA512"],
    // These are only available after the signingKp is defined.
    [setToggle, "signAssertion", true],
    [setToggle, "signResponse", true],
];

// provider_components.schemas.SCIMProviderRequest.yml
//
// - name
// - property_mappings
// - property_mappings_group
// - url
// - verify_certificates
// - token
// - exclude_users_service_account
// - filter_group
//
export const simpleSCIMProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "SCIM Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SCIM Provider")],
    [setTextInput, "url", "http://example.com:8000/"],
    [setTextInput, "token", "insert-real-token-here"],
];

export const completeSCIMProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "SCIM Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SCIM Provider")],
    [setTextInput, "url", "http://example.com:8000/"],
    [setToggle, "verifyCertificates", false],
    [setTextInput, "token", "insert-real-token-here"],
    [setFormGroup, /Protocol settings/, "open"],
    [setFormGroup, /User filtering/, "open"],
    [setToggle, "excludeUsersServiceAccount", false],
    [setSearchSelect, "filterGroup", /authentik Admins/],
    [setFormGroup, /Attribute mapping/, "open"],
    [checkIsPresent, '[name="propertyMappings"]'],
    [checkIsPresent, '[name="propertyMappingsGroup"]'],
];

// provider_components.schemas.ProxyProviderRequest.yml
//
// - name
// - authentication_flow
// - authorization_flow
// - invalidation_flow
// - property_mappings
// - internal_host
// - external_host
// - internal_host_ssl_validation
// - certificate
// - skip_path_regex
// - basic_auth_enabled
// - basic_auth_password_attribute
// - basic_auth_user_attribute
// - mode
// - intercept_header_auth
// - cookie_domain
// - jwks_sources
// - access_token_validity
// - refresh_token_validity
//   - refresh_token_validity is not handled in any of our forms.  On purpose.
// - internal_host_ssl_validation
//   - only on ProxyMode

export const simpleProxyProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Proxy Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [clickToggleGroup, "proxy-type-toggle", "Proxy"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
    [setTextInput, "internalHost", "http://example.com:8001/"],
];

export const simpleForwardAuthProxyProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Forward Auth Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [clickToggleGroup, "proxy-type-toggle", "Forward auth (single application)"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
];

export const simpleForwardAuthDomainProxyProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Forward Auth Domain Level Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [clickToggleGroup, "proxy-type-toggle", "Forward auth (domain level)"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
    [setTextInput, "cookieDomain", "somedomain.tld"],
];

const proxyModeCompletions: TestSequence = [
    [setTextInput, "accessTokenValidity", "hours=36"],
    [setFormGroup, /Advanced protocol settings/, "open"],
    [setSearchSelect, "certificate", /authentik Self-signed Certificate/],
    [checkIsPresent, '[name="propertyMappings"]'],
    [setTextareaInput, "skipPathRegex", "."],
    [setFormGroup, /Authentication settings/, "open"],
    [setToggle, "interceptHeaderAuth", false],
    [setToggle, "basicAuthEnabled", true],
    [setTextInput, "basicAuthUserAttribute", "authorized-user"],
    [setTextInput, "basicAuthPasswordAttribute", "authorized-user-password"],
    [setFormGroup, /Advanced flow settings/, "open"],
    [setSearchSelect, "authenticationFlow", /default-source-authentication/],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [checkIsPresent, '[name="jwtFederationSources"]'],
    [checkIsPresent, '[name="jwtFederationProviders"]'],
];

export const completeProxyProviderForm: TestProvider = () => [
    ...simpleProxyProviderForm(),
    [setToggle, "internalHostSslValidation", false],
    ...proxyModeCompletions,
];

export const completeForwardAuthProxyProviderForm: TestProvider = () => [
    ...simpleForwardAuthProxyProviderForm(),
    ...proxyModeCompletions,
];

export const completeForwardAuthDomainProxyProviderForm: TestProvider = () => [
    ...simpleForwardAuthProxyProviderForm(),
    ...proxyModeCompletions,
];
