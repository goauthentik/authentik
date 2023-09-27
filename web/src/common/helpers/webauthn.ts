import * as base64js from "base64-js";

import { msg } from "@lit/localize";

export function b64enc(buf: Uint8Array): string {
    return base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

export function b64RawEnc(buf: Uint8Array): string {
    return base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_");
}

export function u8arr(input: string): Uint8Array {
    return Uint8Array.from(atob(input.replace(/_/g, "/").replace(/-/g, "+")), (c) =>
        c.charCodeAt(0),
    );
}

export function checkWebAuthnSupport() {
    if ("credentials" in navigator) {
        return;
    }
    if (window.location.protocol === "http:" && window.location.hostname !== "localhost") {
        throw new Error(msg("WebAuthn requires this page to be accessed via HTTPS."));
    }
    throw new Error(msg("WebAuthn not supported by browser."));
}

/**
 * Transforms items in the credentialCreateOptions generated on the server
 * into byte arrays expected by the navigator.credentials.create() call
 */
export function transformCredentialCreateOptions(
    credentialCreateOptions: PublicKeyCredentialCreationOptions,
    userId: string,
): PublicKeyCredentialCreationOptions {
    const user = credentialCreateOptions.user;
    // Because json can't contain raw bytes, the server base64-encodes the User ID
    // So to get the base64 encoded byte array, we first need to convert it to a regular
    // string, then a byte array, re-encode it and wrap that in an array.
    const stringId = decodeURIComponent(escape(window.atob(userId)));
    user.id = u8arr(b64enc(u8arr(stringId)));
    const challenge = u8arr(credentialCreateOptions.challenge.toString());

    const transformedCredentialCreateOptions = Object.assign({}, credentialCreateOptions, {
        challenge,
        user,
    });

    return transformedCredentialCreateOptions;
}

export interface Assertion {
    id: string;
    rawId: string;
    type: string;
    registrationClientExtensions: string;
    response: {
        clientDataJSON: string;
        attestationObject: string;
    };
}

/**
 * Transforms the binary data in the credential into base64 strings
 * for posting to the server.
 * @param {PublicKeyCredential} newAssertion
 */
export function transformNewAssertionForServer(newAssertion: PublicKeyCredential): Assertion {
    const attObj = new Uint8Array(
        (newAssertion.response as AuthenticatorAttestationResponse).attestationObject,
    );
    const clientDataJSON = new Uint8Array(newAssertion.response.clientDataJSON);
    const rawId = new Uint8Array(newAssertion.rawId);

    const registrationClientExtensions = newAssertion.getClientExtensionResults();
    return {
        id: newAssertion.id,
        rawId: b64enc(rawId),
        type: newAssertion.type,
        registrationClientExtensions: JSON.stringify(registrationClientExtensions),
        response: {
            clientDataJSON: b64enc(clientDataJSON),
            attestationObject: b64enc(attObj),
        },
    };
}

export function transformCredentialRequestOptions(
    credentialRequestOptions: PublicKeyCredentialRequestOptions,
): PublicKeyCredentialRequestOptions {
    const challenge = u8arr(credentialRequestOptions.challenge.toString());

    const allowCredentials = (credentialRequestOptions.allowCredentials || []).map(
        (credentialDescriptor) => {
            const id = u8arr(credentialDescriptor.id.toString());
            return Object.assign({}, credentialDescriptor, { id });
        },
    );

    const transformedCredentialRequestOptions = Object.assign({}, credentialRequestOptions, {
        challenge,
        allowCredentials,
    });

    return transformedCredentialRequestOptions;
}

export interface AuthAssertion {
    id: string;
    rawId: string;
    type: string;
    assertionClientExtensions: string;
    response: {
        clientDataJSON: string;
        authenticatorData: string;
        signature: string;
        userHandle: string | null;
    };
}

/**
 * Encodes the binary data in the assertion into strings for posting to the server.
 * @param {PublicKeyCredential} newAssertion
 */
export function transformAssertionForServer(newAssertion: PublicKeyCredential): AuthAssertion {
    const response = newAssertion.response as AuthenticatorAssertionResponse;
    const authData = new Uint8Array(response.authenticatorData);
    const clientDataJSON = new Uint8Array(response.clientDataJSON);
    const rawId = new Uint8Array(newAssertion.rawId);
    const sig = new Uint8Array(response.signature);
    const assertionClientExtensions = newAssertion.getClientExtensionResults();

    return {
        id: newAssertion.id,
        rawId: b64enc(rawId),
        type: newAssertion.type,
        assertionClientExtensions: JSON.stringify(assertionClientExtensions),

        response: {
            clientDataJSON: b64RawEnc(clientDataJSON),
            signature: b64RawEnc(sig),
            authenticatorData: b64RawEnc(authData),
            userHandle: null,
        },
    };
}
