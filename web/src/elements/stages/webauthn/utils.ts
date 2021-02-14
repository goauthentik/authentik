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

async function fetchJSON(url: string, options: RequestInit): Promise<any> {
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
export function transformCredentialCreateOptions(credentialCreateOptions: PublicKeyCredentialCreationOptions) {
    let challenge = credentialCreateOptions.challenge;
    const user = credentialCreateOptions.user;
    user.id = Uint8Array.from(
        atob(credentialCreateOptions.user.id.toString()
            .replace(/\_/g, "/")
            .replace(/\-/g, "+")
        ),
        c => c.charCodeAt(0));
    challenge = Uint8Array.from(
        atob(credentialCreateOptions.challenge.toString()
            .replace(/\_/g, "/")
            .replace(/\-/g, "+")
        ),
        c => c.charCodeAt(0));

    const transformedCredentialCreateOptions = Object.assign(
        {}, credentialCreateOptions,
        { challenge, user });

    return transformedCredentialCreateOptions;
}

/**
 * Transforms the binary data in the credential into base64 strings
 * for posting to the server.
 * @param {PublicKeyCredential} newAssertion
 */
export function transformNewAssertionForServer(newAssertion: PublicKeyCredential) {
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
export async function postNewAssertionToServer (assertionDataForServer: {
    [key: string]: string;
}) {
    const formData = new FormData();
    Object.entries(assertionDataForServer).forEach(([key, value]) => {
        formData.set(key, value);
    });

    return await fetchJSON(
        "/-/user/webauthn/verify-credential-info/", {
        method: "POST",
        body: formData
    });
}

/**
 * Get PublicKeyCredentialRequestOptions for this user from the server
 * formData of the registration form
 * @param {FormData} formData
 */
export async function getCredentialCreateOptionsFromServer() {
    return await fetchJSON(
        "/-/user/webauthn/begin-activate/",
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
export async function getCredentialRequestOptionsFromServer() {
    return await fetchJSON(
        "/-/user/webauthn/begin-assertion/",
        {
            method: "POST",
        }
    );
}

export function transformCredentialRequestOptions(credentialRequestOptionsFromServer: PublicKeyCredentialRequestOptions) {
    let { challenge, allowCredentials } = credentialRequestOptionsFromServer;

    challenge = Uint8Array.from(
        atob(challenge.toString().replace(/\_/g, "/").replace(/\-/g, "+")), c => c.charCodeAt(0));

    allowCredentials = allowCredentials!.map(credentialDescriptor => {
        const id = Uint8Array.from(atob(credentialDescriptor.id.toString().replace(/\_/g, "/").replace(/\-/g, "+")), c => c.charCodeAt(0));
        return Object.assign({}, credentialDescriptor, { id });
    });

    const transformedCredentialRequestOptions = Object.assign(
        {},
        credentialRequestOptionsFromServer,
        { challenge, allowCredentials });

    return transformedCredentialRequestOptions;
}

/**
 * Encodes the binary data in the assertion into strings for posting to the server.
 * @param {PublicKeyCredential} newAssertion
 */
export function transformAssertionForServer(newAssertion: PublicKeyCredential) {
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
export async function postAssertionToServer(assertionDataForServer: {
    [key: string]: string;
}) {
    const formData = new FormData();
    Object.entries(assertionDataForServer).forEach(([key, value]) => {
        formData.set(key, value);
    });

    return await fetchJSON(
        "/-/user/webauthn/verify-assertion/", {
            method: "POST",
            body: formData
    });
}
