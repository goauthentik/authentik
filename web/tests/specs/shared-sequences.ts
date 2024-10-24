import {
    clickButton,
    setFormGroup,
    setSearchSelect,
    setTextInput,
    setTypeCreate,
} from "pageobjects/controls.js";

import { randomId } from "../utils/index.js";

const newObjectName = (prefix: string) => `${prefix} - ${randomId()}`;

export const simpleOAuth2ProviderForm = () => [
    [setTypeCreate, "selectProviderType", "OAuth2/OpenID Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Oauth2 Provider")],
    [setSearchSelect, "authorizationFlow", "default-provider-authorization-explicit-consent"],
];

export const simpleLDAPProviderForm = () => [
    [setTypeCreate, "selectProviderType", "LDAP Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New LDAP Provider")],
    // This will never not weird me out.
    [setSearchSelect, "authorizationFlow", "default-authentication-flow"],
    [setFormGroup, /Flow settings/, "open"],
    [setSearchSelect, "invalidationFlow", "default-invalidation-flow"],
];

export const simpleRadiusProviderForm = () => [
    [setTypeCreate, "selectProviderType", "Radius Provider"],
    [clickButton, "Next"],
    [setTextInput, "name", newObjectName("New Radius Provider")],
    [setSearchSelect, "authorizationFlow", "default-authentication-flow"],
];
