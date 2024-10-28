import {
    clickButton,
    clickToggleGroup,
    setFormGroup,
    setSearchSelect,
    setTextInput,
    setTypeCreate,
} from "pageobjects/controls.js";

import { randomId } from "../utils/index.js";

const newObjectName = (prefix: string) => `${prefix} - ${randomId()}`;

export type TestInteraction =
    | [typeof clickButton, ...Parameters<typeof clickButton>]
    | [typeof clickToggleGroup, ...Parameters<typeof clickToggleGroup>]
    | [typeof setFormGroup, ...Parameters<typeof setFormGroup>]
    | [typeof setSearchSelect, ...Parameters<typeof setSearchSelect>]
    | [typeof setTextInput, ...Parameters<typeof setTextInput>]
    | [typeof setTypeCreate, ...Parameters<typeof setTypeCreate>];

export type TestSequence = TestInteraction[];

export type TestProvider = () => TestSequence;

export const simpleOAuth2ProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "OAuth2/OpenID Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Oauth2 Provider")],
    [setSearchSelect, "authorizationFlow", "default-provider-authorization-explicit-consent"],
];

export const simpleLDAPProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "LDAP Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New LDAP Provider")],
    // This will never not weird me out.
    [setFormGroup, /Flow settings/, "open"],
    [setSearchSelect, "authorizationFlow", "default-authentication-flow"],
    [setSearchSelect, "invalidationFlow", "default-invalidation-flow"],
];

export const simpleRadiusProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Radius Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Radius Provider")],
    [setSearchSelect, "authorizationFlow", "default-authentication-flow"],
];

export const simpleSAMLProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "SAML Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SAML Provider")],
    [setSearchSelect, "authorizationFlow", "default-provider-authorization-explicit-consent"],
    [setTextInput, "acsUrl", "http://example.com:8000/"],
];

export const simpleSCIMProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "SCIM Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New SCIM Provider")],
    [setTextInput, "url", "http://example.com:8000/"],
    [setTextInput, "token", "insert-real-token-here"],
];

export const simpleProxyProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Proxy Provider")],
    [setSearchSelect, "authorizationFlow", "default-provider-authorization-explicit-consent"],
    [clickToggleGroup, "proxy-type-toggle", "Proxy"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
    [setTextInput, "internalHost", "http://example.com:8001/"],
];

export const simpleForwardAuthProxyProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Forward Auth Provider")],
    [setSearchSelect, "authorizationFlow", "default-provider-authorization-explicit-consent"],
    [clickToggleGroup, "proxy-type-toggle", "Forward auth (single application)"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
];

export const simpleForwardAuthDomainProxyProviderForm: TestProvider = () => [
    [setTypeCreate, "selectProviderType", "Proxy Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Forward Auth Domain Level Provider")],
    [setSearchSelect, "authorizationFlow", "default-provider-authorization-explicit-consent"],
    [clickToggleGroup, "proxy-type-toggle", "Forward auth (domain level)"],
    [setTextInput, "externalHost", "http://example.com:8000/"],
    [setTextInput, "cookieDomain", "somedomain.tld"],
];
