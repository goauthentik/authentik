/**
 * @file WebAuthn utilities.
 *
 * @remarks
 *
 * This duplicates much of the logic in the main web app's WebAuthn utilities.
 * Can we share this code while keeping IE11 support?
 */
import { fromByteArray } from "base64-js";

//@ts-check

//#region Type Definitions

/**
 * @typedef {object} Assertion
 * @property {string} id
 * @property {string} rawId
 * @property {string} type
 * @property {string} registrationClientExtensions
 * @property {object} response
 * @property {string} response.clientDataJSON
 * @property {string} response.attestationObject
 */

/**
 * @typedef {object} AuthAssertion
 * @property {string} id
 * @property {string} rawId
 * @property {string} type
 * @property {string} assertionClientExtensions
 * @property {object} response
 * @property {string} response.clientDataJSON
 * @property {string} response.authenticatorData
 * @property {string} response.signature
 * @property {string | null} response.userHandle
 */

//#endregion

//#region Encoding/Decoding

/**
 * Encodes a byte array into a URL-safe base64 string.
 *
 * @param {Uint8Array} buffer
 * @returns {string}
 */
export function encodeBase64(buffer) {
    return fromByteArray(buffer).replace(/\+/g, "-").replace(/\//g, "_").replace(/[=]/g, "");
}

/**
 * Encodes a byte array into a base64 string without URL-safe encoding, i.e., with padding.
 * @param {Uint8Array} buffer
 * @returns {string}
 */
export function encodeBase64Raw(buffer) {
    return fromByteArray(buffer).replace(/\+/g, "-").replace(/\//g, "_");
}

/**
 * Decodes a base64 string into a byte array.
 *
 * @param {string} input
 * @returns {Uint8Array}
 */
export function decodeBase64(input) {
    return Uint8Array.from(atob(input.replace(/_/g, "/").replace(/-/g, "+")), (c) =>
        c.charCodeAt(0),
    );
}

//#endregion

//#region Utility Functions

/**
 * Checks if the browser supports WebAuthn.
 *
 * @returns {boolean}
 */
export function isWebAuthnSupported() {
    if ("credentials" in navigator) return true;

    if (window.location.protocol === "http:" && window.location.hostname !== "localhost") {
        console.warn("WebAuthn requires this page to be accessed via HTTPS.");
        return false;
    }

    console.warn("WebAuthn not supported by browser.");
    return false;
}

/**
 * Asserts that the browser supports WebAuthn and that we're in a secure context.
 *
 * @throws {Error} If WebAuthn is not supported.
 */
export function assertWebAuthnSupport() {
    // Is the navigator exposing the credentials API?
    if ("credentials" in navigator) return;

    if (window.location.protocol === "http:" && window.location.hostname !== "localhost") {
        throw new Error("WebAuthn requires this page to be accessed via HTTPS.");
    }
    throw new Error("WebAuthn not supported by browser.");
}

/**
 * Transforms items in the credentialCreateOptions generated on the server
 * into byte arrays expected by the navigator.credentials.create() call
 * @param {PublicKeyCredentialCreationOptions} credentialCreateOptions
 * @param {string} userID
 * @returns {PublicKeyCredentialCreationOptions}
 */
export function transformCredentialCreateOptions(credentialCreateOptions, userID) {
    const user = credentialCreateOptions.user;
    // Because json can't contain raw bytes, the server base64-encodes the User ID
    // So to get the base64 encoded byte array, we first need to convert it to a regular
    // string, then a byte array, re-encode it and wrap that in an array.
    const stringId = decodeURIComponent(window.atob(userID));

    user.id = decodeBase64(encodeBase64(decodeBase64(stringId)));
    const challenge = decodeBase64(credentialCreateOptions.challenge.toString());

    return {
        ...credentialCreateOptions,
        challenge,
        user,
    };
}

/**
 * Transforms the binary data in the credential into base64 strings
 * for posting to the server.
 *
 * @param {PublicKeyCredential} newAssertion
 * @returns {Assertion}
 */
export function transformNewAssertionForServer(newAssertion) {
    const response = /** @type {AuthenticatorAttestationResponse} */ (newAssertion.response);

    const attObj = new Uint8Array(response.attestationObject);
    const clientDataJSON = new Uint8Array(newAssertion.response.clientDataJSON);
    const rawId = new Uint8Array(newAssertion.rawId);

    const registrationClientExtensions = newAssertion.getClientExtensionResults();

    return {
        id: newAssertion.id,
        rawId: encodeBase64(rawId),
        type: newAssertion.type,
        registrationClientExtensions: JSON.stringify(registrationClientExtensions),
        response: {
            clientDataJSON: encodeBase64(clientDataJSON),
            attestationObject: encodeBase64(attObj),
        },
    };
}

/**
 *  Transforms  the items in the credentialRequestOptions generated on the server
 *
 * @param {PublicKeyCredentialRequestOptions} credentialRequestOptions
 * @returns {PublicKeyCredentialRequestOptions}
 */
export function transformCredentialRequestOptions(credentialRequestOptions) {
    const challenge = decodeBase64(credentialRequestOptions.challenge.toString());

    const allowCredentials = (credentialRequestOptions.allowCredentials || []).map(
        (credentialDescriptor) => {
            const id = decodeBase64(credentialDescriptor.id.toString());
            return Object.assign({}, credentialDescriptor, { id });
        },
    );

    return Object.assign({}, credentialRequestOptions, {
        challenge,
        allowCredentials,
    });
}

/**
 * Encodes the binary data in the assertion into strings for posting to the server.
 * @param {PublicKeyCredential} newAssertion
 * @returns {AuthAssertion}
 */
export function transformAssertionForServer(newAssertion) {
    const response = /** @type {AuthenticatorAssertionResponse} */ (newAssertion.response);

    const authData = new Uint8Array(response.authenticatorData);
    const clientDataJSON = new Uint8Array(response.clientDataJSON);
    const rawId = new Uint8Array(newAssertion.rawId);
    const sig = new Uint8Array(response.signature);
    const assertionClientExtensions = newAssertion.getClientExtensionResults();

    return {
        id: newAssertion.id,
        rawId: encodeBase64(rawId),
        type: newAssertion.type,
        assertionClientExtensions: JSON.stringify(assertionClientExtensions),

        response: {
            clientDataJSON: encodeBase64Raw(clientDataJSON),
            signature: encodeBase64Raw(sig),
            authenticatorData: encodeBase64Raw(authData),
            userHandle: null,
        },
    };
}
