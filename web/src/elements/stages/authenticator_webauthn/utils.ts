import * as base64js from "base64-js";

export function b64enc(buf: Uint8Array): string {
    return base64js.fromByteArray(buf)
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=/g, "");
}

export function b64RawEnc(buf: Uint8Array): string {
    return base64js.fromByteArray(buf)
        .replace(/\+/g, "-")
        .replace(/\//g, "_");
}

export function hexEncode(buf: Uint8Array): string {
    return Array.from(buf)
        .map(function (x) {
            return ("0" + x.toString(16)).substr(-2);
        })
        .join("");
}

export interface GenericResponse {
    fail?: string;
    success?: string;
    [key: string]: string | number | GenericResponse | undefined;
}

async function fetchJSON(url: string, options: RequestInit): Promise<GenericResponse> {
    const response = await fetch(url, options);
    const body = await response.json();
    if (body.fail)
        throw body.fail;
    return body;
}

/**
 * Transforms items in the credentialCreateOptions generated on the server
 * into byte arrays expected by the navigator.credentials.create() call
 */
export function transformCredentialCreateOptions(credentialCreateOptions: PublicKeyCredentialCreationOptions): PublicKeyCredentialCreationOptions {
    const user = credentialCreateOptions.user;
    user.id = u8arr(credentialCreateOptions.user.id.toString());
    const challenge = u8arr(credentialCreateOptions.challenge.toString());

    const transformedCredentialCreateOptions = Object.assign(
        {}, credentialCreateOptions,
        { challenge, user });

    return transformedCredentialCreateOptions;
}

export interface Assertion {
    id: string;
    rawId: string;
    type: string;
    attObj: string;
    clientData: string;
    registrationClientExtensions: string;
}

/**
 * Transforms the binary data in the credential into base64 strings
 * for posting to the server.
 * @param {PublicKeyCredential} newAssertion
 */
export function transformNewAssertionForServer(newAssertion: PublicKeyCredential): Assertion {
    const attObj = new Uint8Array(
        (<AuthenticatorAttestationResponse>newAssertion.response).attestationObject);
    const clientDataJSON = new Uint8Array(
        newAssertion.response.clientDataJSON);
    const rawId = new Uint8Array(
        newAssertion.rawId);

    const registrationClientExtensions = newAssertion.getClientExtensionResults();
    return {
        id: newAssertion.id,
        rawId: b64enc(rawId),
        type: newAssertion.type,
        attObj: b64enc(attObj),
        clientData: b64enc(clientDataJSON),
        registrationClientExtensions: JSON.stringify(registrationClientExtensions)
    };
}

/**
 * Post the assertion to the server for validation and logging the user in.
 * @param {Object} assertionDataForServer
 */
export async function postNewAssertionToServer(assertionDataForServer: Assertion): Promise<GenericResponse> {
    const formData = new FormData();
    Object.entries(assertionDataForServer).forEach(([key, value]) => {
        formData.set(key, value);
    });

    return await fetchJSON(
        "/-/user/authenticator/webauthn/verify-credential-info/", {
        method: "POST",
        body: formData
    });
}

/**
 * Get PublicKeyCredentialRequestOptions for this user from the server
 * formData of the registration form
 * @param {FormData} formData
 */
export async function getCredentialCreateOptionsFromServer(): Promise<GenericResponse> {
    return await fetchJSON(
        "/-/user/authenticator/webauthn/begin-activate/",
        {
            method: "POST",
        }
    );
}


/**
 * Get PublicKeyCredentialRequestOptions for this user from the server
 * formData of the registration form
 * @param {FormData} formData
 */
export async function getCredentialRequestOptionsFromServer(): Promise<GenericResponse> {
    return await fetchJSON(
        "/-/user/authenticator/webauthn/begin-assertion/",
        {
            method: "POST",
        }
    );
}

function u8arr(input: string): Uint8Array {
    return Uint8Array.from(atob(input.replace(/_/g, "/").replace(/-/g, "+")), c => c.charCodeAt(0));
}

export function transformCredentialRequestOptions(credentialRequestOptions: PublicKeyCredentialRequestOptions): PublicKeyCredentialRequestOptions {
    const challenge = u8arr(credentialRequestOptions.challenge.toString());

    const allowCredentials = (credentialRequestOptions.allowCredentials || []).map(credentialDescriptor => {
        const id = u8arr(credentialDescriptor.id.toString());
        return Object.assign({}, credentialDescriptor, { id });
    });

    const transformedCredentialRequestOptions = Object.assign(
        {},
        credentialRequestOptions,
        { challenge, allowCredentials });

    return transformedCredentialRequestOptions;
}

export interface AuthAssertion {
    id: string;
    rawId: string;
    type: string;
    clientData: string;
    authData: string;
    signature: string;
    assertionClientExtensions: string;
}

/**
 * Encodes the binary data in the assertion into strings for posting to the server.
 * @param {PublicKeyCredential} newAssertion
 */
export function transformAssertionForServer(newAssertion: PublicKeyCredential): AuthAssertion{
    const response = <AuthenticatorAssertionResponse> newAssertion.response;
    const authData = new Uint8Array(response.authenticatorData);
    const clientDataJSON = new Uint8Array(response.clientDataJSON);
    const rawId = new Uint8Array(newAssertion.rawId);
    const sig = new Uint8Array(response.signature);
    const assertionClientExtensions = newAssertion.getClientExtensionResults();

    return {
        id: newAssertion.id,
        rawId: b64enc(rawId),
        type: newAssertion.type,
        authData: b64RawEnc(authData),
        clientData: b64RawEnc(clientDataJSON),
        signature: hexEncode(sig),
        assertionClientExtensions: JSON.stringify(assertionClientExtensions)
    };
}

/**
 * Post the assertion to the server for validation and logging the user in.
 * @param {Object} assertionDataForServer
 */
export async function postAssertionToServer(assertionDataForServer: Assertion): Promise<GenericResponse> {
    const formData = new FormData();
    Object.entries(assertionDataForServer).forEach(([key, value]) => {
        formData.set(key, value);
    });

    return await fetchJSON(
        "/-/user/authenticator/webauthn/verify-assertion/", {
            method: "POST",
            body: formData
    });
}
