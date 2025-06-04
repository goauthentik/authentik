import { ascii_letters, digits, randomString } from "#common/utils";
import { randomId } from "#elements/utils/randomId";
import {
    type TestAction,
    type TestSequence,
    assertVisible,
    clickButton,
    clickToggleGroup,
    setRadio,
    setSearchSelect,
    setTextInput,
    setTextareaInput,
    setToggle,
    setTypeCreate,
    toggleFormGroup,
} from "#tests/utils/controls";
import { IDGenerator } from "@goauthentik/core/id";

const newObjectName = (prefix: string) => `${prefix} - ${IDGenerator.next()}`;

export const simpleOAuth2ProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "OAuth2/OpenID Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Oauth2 Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
];

export const completeOAuth2ProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "OAuth2/OpenID Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Oauth2 Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [toggleFormGroup, /Protocol settings/, true],
    [setRadio, "clientType", "Public"],
    // Switch back so we can make sure `clientSecret` is available.
    [setRadio, "clientType", "Confidential"],
    [assertVisible, '[name="clientId"]'],
    [assertVisible, '[name="clientSecret"]'],
    [setSearchSelect, "signingKey", /authentik Self-signed Certificate/],
    [setSearchSelect, "encryptionKey", /authentik Self-signed Certificate/],
    [toggleFormGroup, /Advanced flow settings/, true],
    [setSearchSelect, "authenticationFlow", /default-source-authentication/],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [toggleFormGroup, /Advanced protocol settings/, true],
    [setTextInput, "accessCodeValidity", "minutes=2"],
    [setTextInput, "accessTokenValidity", "minutes=10"],
    [setTextInput, "refreshTokenValidity", "days=40"],
    [setToggle, "includeClaimsInIdToken", false],
    [assertVisible, '[name="redirectUris"]'],
    [setRadio, "subMode", "Based on the User's username"],
    [setRadio, "issuerMode", "Same identifier is used for all providers"],
    [toggleFormGroup, /Machine-to-Machine authentication settings/, true],
    [assertVisible, '[name="jwtFederationSources"]'],
    [assertVisible, '[name="jwtFederationProviders"]'],
];

export const simpleLDAPProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "LDAP Provider"],
    [clickButton, "Next"],
    // [setTextInput, "name", newObjectName("New LDAP Provider")],
    // // This will never not weird me out.
    // [toggleFormGroup, /Flow settings/, true],
    // [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
    // [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
];

export const completeLDAPProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "LDAP Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New LDAP Provider")],
    [toggleFormGroup, /Flow settings/, true],
    [toggleFormGroup, /Protocol settings/, true],
    [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [setTextInput, "baseDn", "DC=ldap-2,DC=goauthentik,DC=io"],
    [setSearchSelect, "certificate", /authentik Self-signed Certificate/],
    [assertVisible, '[name="tlsServerName"]'],
    [setTextInput, "uidStartNumber", "2001"],
    [setTextInput, "gidStartNumber", "4001"],
    [setRadio, "searchMode", "Direct querying"],
    [setRadio, "bindMode", "Direct binding"],
    [setToggle, "mfaSupport", false],
];

export const simpleRadiusProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "Radius Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Radius Provider")],
    [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
];

export const completeRadiusProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "Radius Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Radius Provider")],
    [setSearchSelect, "authorizationFlow", /default-authentication-flow/],
    [toggleFormGroup, /Advanced flow settings/, true],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [toggleFormGroup, /Protocol settings/, true],
    [setToggle, "mfaSupport", false],
    [setTextInput, "clientNetworks", ""],
    [setTextInput, "clientNetworks", "0.0.0.0/0, ::/0"],
    [setTextInput, "sharedSecret", randomString(128, ascii_letters + digits)],
    [assertVisible, '[name="propertyMappings"]'],
];

export const simpleSAMLProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "SAML Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SAML Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [setTextInput, "acsUrl", "http://example.com:8000/"],
];

export const completeSAMLProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "SAML Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SAML Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [setTextInput, "acsUrl", "http://example.com:8000/"],
    [setTextInput, "issuer", "someone-else"],
    [setRadio, "spBinding", "Post"],
    [setTextInput, "audience", ""],
    [toggleFormGroup, /Advanced flow settings/, true],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [setSearchSelect, "authenticationFlow", /default-source-authentication/],
    [toggleFormGroup, /Advanced protocol settings/, true],
    [assertVisible, '[name="propertyMappings"]'],
    [setSearchSelect, "signingKp", /authentik Self-signed Certificate/],
    [setSearchSelect, "verificationKp", /authentik Self-signed Certificate/],
    [setSearchSelect, "encryptionKp", /authentik Self-signed Certificate/],
    [setSearchSelect, "nameIdMapping", /authentik default SAML Mapping. Username/],
    [setTextInput, "assertionValidNotBefore", "minutes=-10"],
    [setTextInput, "assertionValidNotOnOrAfter", "minutes=10"],
    [setTextInput, "sessionValidNotOnOrAfter", "minutes=172800"],
    [assertVisible, '[name="defaultRelayState"]'],
    [setRadio, "digestAlgorithm", "SHA512"],
    [setRadio, "signatureAlgorithm", "RSA-SHA512"],
    // These are only available after the signingKp is defined.
    [setToggle, "signAssertion", true],
    [setToggle, "signResponse", true],
];

export const simpleSCIMProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "SCIM Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SCIM Provider")],
    [setTextInput, "url", "http://example.com:8000/"],
    [setTextInput, "token", "insert-real-token-here"],
];

export const completeSCIMProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "SCIM Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SCIM Provider")],
    [setTextInput, "url", "http://example.com:8000/"],
    [setToggle, "verifyCertificates", false],
    [setTextInput, "token", "insert-real-token-here"],
    [toggleFormGroup, /Protocol settings/, true],
    [toggleFormGroup, /User filtering/, true],
    [setToggle, "excludeUsersServiceAccount", false],
    [setSearchSelect, "filterGroup", /authentik Admins/],
    [toggleFormGroup, /Attribute mapping/, true],
    [assertVisible, '[name="propertyMappings"]'],
    [assertVisible, '[name="propertyMappingsGroup"]'],
];

export const simpleProxyProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Proxy Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [clickToggleGroup, "proxy-type-toggle", "Proxy"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
    [setTextInput, "internalHost", "http://example.com:8001/"],
];

export const simpleForwardAuthProxyProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Forward Auth Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [clickToggleGroup, "proxy-type-toggle", "Forward auth (single application)"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
];

export const simpleForwardAuthDomainProxyProviderForm: TestSequence = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Forward Auth Domain Level Provider")],
    [setSearchSelect, "authorizationFlow", /default-provider-authorization-explicit-consent/],
    [clickToggleGroup, "proxy-type-toggle", "Forward auth (domain level)"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
    [setTextInput, "cookieDomain", "somedomain.tld"],
];

const proxyModeCompletions: TestAction[] = [
    [setTextInput, "accessTokenValidity", "hours=36"],
    [toggleFormGroup, /Advanced protocol settings/, true],
    [setSearchSelect, "certificate", /authentik Self-signed Certificate/],
    [assertVisible, '[name="propertyMappings"]'],
    [setTextareaInput, "skipPathRegex", "."],
    [toggleFormGroup, /Authentication settings/, true],
    [setToggle, "interceptHeaderAuth", false],
    [setToggle, "basicAuthEnabled", true],
    [setTextInput, "basicAuthUserAttribute", "authorized-user"],
    [setTextInput, "basicAuthPasswordAttribute", "authorized-user-password"],
    [toggleFormGroup, /Advanced flow settings/, true],
    [setSearchSelect, "authenticationFlow", /default-source-authentication/],
    [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
    [assertVisible, '[name="jwtFederationSources"]'],
    [assertVisible, '[name="jwtFederationProviders"]'],
];

export const completeProxyProviderForm: TestSequence = () => [
    ...simpleProxyProviderForm(),
    [setToggle, "internalHostSslValidation", false],
    ...proxyModeCompletions,
];

export const completeForwardAuthProxyProviderForm: TestSequence = () => [
    ...simpleForwardAuthProxyProviderForm(),
    ...proxyModeCompletions,
];

export const completeForwardAuthDomainProxyProviderForm: TestSequence = () => [
    ...simpleForwardAuthProxyProviderForm(),
    ...proxyModeCompletions,
];
