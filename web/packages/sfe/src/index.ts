import { fromByteArray } from "base64-js";
import "formdata-polyfill";
import $ from "jquery";
import "weakmap-polyfill";

import {
    type AuthenticatorValidationChallenge,
    type AutosubmitChallenge,
    type ChallengeTypes,
    ChallengeTypesFromJSON,
    type ContextualFlowInfo,
    type DeviceChallenge,
    type ErrorDetail,
    type IdentificationChallenge,
    type PasswordChallenge,
    type RedirectChallenge,
} from "@goauthentik/api";

interface GlobalAuthentik {
    brand: {
        branding_logo: string;
    };
    api: {
        base: string;
    };
}

function ak(): GlobalAuthentik {
    return (
        window as unknown as {
            authentik: GlobalAuthentik;
        }
    ).authentik;
}

class SimpleFlowExecutor {
    challenge?: ChallengeTypes;
    flowSlug: string;
    container: HTMLDivElement;

    constructor(container: HTMLDivElement) {
        this.flowSlug = window.location.pathname.split("/")[3];
        this.container = container;
    }

    get apiURL() {
        return `${ak().api.base}api/v3/flows/executor/${this.flowSlug}/?query=${encodeURIComponent(window.location.search.substring(1))}`;
    }

    loading() {
        this.container.innerHTML = `<div class="d-flex justify-content-center">
            <div class="spinner-border spinner-border-md" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        </div>`;
    }

    start() {
        this.loading();
        $.ajax({
            type: "GET",
            url: this.apiURL,
            success: (data) => {
                this.challenge = ChallengeTypesFromJSON(data);
                this.renderChallenge();
            },
        });
    }

    submit(data: { [key: string]: unknown } | FormData) {
        $("button[type=submit]").addClass("disabled")
            .html(`<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                <span role="status">Loading...</span>`);
        let finalData: { [key: string]: unknown } = {};
        if (data instanceof FormData) {
            finalData = {};
            data.forEach((value, key) => {
                finalData[key] = value;
            });
        } else {
            finalData = data;
        }
        $.ajax({
            type: "POST",
            url: this.apiURL,
            data: JSON.stringify(finalData),
            success: (data) => {
                this.challenge = ChallengeTypesFromJSON(data);
                this.renderChallenge();
            },
            contentType: "application/json",
            dataType: "json",
        });
    }

    renderChallenge() {
        switch (this.challenge?.component) {
            case "ak-stage-identification":
                new IdentificationStage(this, this.challenge).render();
                return;
            case "ak-stage-password":
                new PasswordStage(this, this.challenge).render();
                return;
            case "xak-flow-redirect":
                new RedirectStage(this, this.challenge).render();
                return;
            case "ak-stage-autosubmit":
                new AutosubmitStage(this, this.challenge).render();
                return;
            case "ak-stage-authenticator-validate":
                new AuthenticatorValidateStage(this, this.challenge).render();
                return;
            default:
                this.container.innerText = "Unsupported stage: " + this.challenge?.component;
                return;
        }
    }
}

export interface FlowInfoChallenge {
    flowInfo?: ContextualFlowInfo;
    responseErrors?: {
        [key: string]: Array<ErrorDetail>;
    };
}

class Stage<T extends FlowInfoChallenge> {
    constructor(
        public executor: SimpleFlowExecutor,
        public challenge: T,
    ) {}

    error(fieldName: string) {
        if (!this.challenge.responseErrors) {
            return [];
        }
        return this.challenge.responseErrors[fieldName] || [];
    }

    renderInputError(fieldName: string) {
        return `${this.error(fieldName)
            .map((error) => {
                return `<div class="invalid-feedback">
                    ${error.string}
                </div>`;
            })
            .join("")}`;
    }

    renderNonFieldErrors() {
        return `${this.error("non_field_errors")
            .map((error) => {
                return `<div class="alert alert-danger" role="alert">
                    ${error.string}
                </div>`;
            })
            .join("")}`;
    }

    html(html: string) {
        this.executor.container.innerHTML = html;
    }

    render() {
        throw new Error("Abstract method");
    }
}

const IS_INVALID = "is-invalid";

class IdentificationStage extends Stage<IdentificationChallenge> {
    render() {
        this.html(`
            <form id="ident-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                ${
                    this.challenge.applicationPre
                        ? `<p>
                              Log in to continue to ${this.challenge.applicationPre}.
                          </p>`
                        : ""
                }
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control" name="uid_field" placeholder="Email / Username">
                </div>
                ${
                    this.challenge.passwordFields
                        ? `<div class="form-label-group my-3 has-validation">
                                <input type="password" class="form-control ${this.error("password").length > 0 ? IS_INVALID : ""}" name="password" placeholder="Password">
                                ${this.renderInputError("password")}
                        </div>`
                        : ""
                }
                ${this.renderNonFieldErrors()}
                <button class="btn btn-primary w-100 py-2" type="submit">${this.challenge.primaryAction}</button>
            </form>`);
        $("#ident-form input[name=uid_field]").trigger("focus");
        $("#ident-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target as HTMLFormElement);
            this.executor.submit(data);
        });
    }
}

class PasswordStage extends Stage<PasswordChallenge> {
    render() {
        this.html(`
            <form id="password-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                <div class="form-label-group my-3">
                    <input type="text" readonly class="form-control-plaintext" value="Welcome, ${this.challenge?.pendingUser}.">
                </div>
                <div class="form-label-group my-3 has-validation">
                    <input type="password" autofocus class="form-control ${this.error("password").length > 0 ? IS_INVALID : ""}" name="password" placeholder="Password">
                    ${this.renderInputError("password")}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);
        $("#password-form input").trigger("focus");
        $("#password-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target as HTMLFormElement);
            this.executor.submit(data);
        });
    }
}

class RedirectStage extends Stage<RedirectChallenge> {
    render() {
        window.location.assign(this.challenge.to);
    }
}

class AutosubmitStage extends Stage<AutosubmitChallenge> {
    render() {
        this.html(`
            <form id="autosubmit-form" action="${this.challenge.url}" method="POST">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                ${Object.entries(this.challenge.attrs).map(([key, value]) => {
                    return `<input
                            type="hidden"
                            name="${key}"
                            value="${value}"
                        />`;
                })}
                <div class="d-flex justify-content-center">
                    <div class="spinner-border" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                </div>
            </form>`);
        $("#autosubmit-form").submit();
    }
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

class AuthenticatorValidateStage extends Stage<AuthenticatorValidationChallenge> {
    deviceChallenge?: DeviceChallenge;

    b64enc(buf: Uint8Array): string {
        return fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
    }

    b64RawEnc(buf: Uint8Array): string {
        return fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_");
    }

    u8arr(input: string): Uint8Array {
        return Uint8Array.from(atob(input.replace(/_/g, "/").replace(/-/g, "+")), (c) =>
            c.charCodeAt(0),
        );
    }

    checkWebAuthnSupport(): boolean {
        if ("credentials" in navigator) {
            return true;
        }
        if (window.location.protocol === "http:" && window.location.hostname !== "localhost") {
            console.warn("WebAuthn requires this page to be accessed via HTTPS.");
            return false;
        }
        console.warn("WebAuthn not supported by browser.");
        return false;
    }

    /**
     * Transforms items in the credentialCreateOptions generated on the server
     * into byte arrays expected by the navigator.credentials.create() call
     */
    transformCredentialCreateOptions(
        credentialCreateOptions: PublicKeyCredentialCreationOptions,
        userId: string,
    ): PublicKeyCredentialCreationOptions {
        const user = credentialCreateOptions.user;
        // Because json can't contain raw bytes, the server base64-encodes the User ID
        // So to get the base64 encoded byte array, we first need to convert it to a regular
        // string, then a byte array, re-encode it and wrap that in an array.
        const stringId = decodeURIComponent(window.atob(userId));
        user.id = this.u8arr(this.b64enc(this.u8arr(stringId)));
        const challenge = this.u8arr(credentialCreateOptions.challenge.toString());

        return Object.assign({}, credentialCreateOptions, {
            challenge,
            user,
        });
    }

    /**
     * Transforms the binary data in the credential into base64 strings
     * for posting to the server.
     * @param {PublicKeyCredential} newAssertion
     */
    transformNewAssertionForServer(newAssertion: PublicKeyCredential): Assertion {
        const attObj = new Uint8Array(
            (newAssertion.response as AuthenticatorAttestationResponse).attestationObject,
        );
        const clientDataJSON = new Uint8Array(newAssertion.response.clientDataJSON);
        const rawId = new Uint8Array(newAssertion.rawId);

        const registrationClientExtensions = newAssertion.getClientExtensionResults();
        return {
            id: newAssertion.id,
            rawId: this.b64enc(rawId),
            type: newAssertion.type,
            registrationClientExtensions: JSON.stringify(registrationClientExtensions),
            response: {
                clientDataJSON: this.b64enc(clientDataJSON),
                attestationObject: this.b64enc(attObj),
            },
        };
    }

    transformCredentialRequestOptions(
        credentialRequestOptions: PublicKeyCredentialRequestOptions,
    ): PublicKeyCredentialRequestOptions {
        const challenge = this.u8arr(credentialRequestOptions.challenge.toString());

        const allowCredentials = (credentialRequestOptions.allowCredentials || []).map(
            (credentialDescriptor) => {
                const id = this.u8arr(credentialDescriptor.id.toString());
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
     */
    transformAssertionForServer(newAssertion: PublicKeyCredential): AuthAssertion {
        const response = newAssertion.response as AuthenticatorAssertionResponse;
        const authData = new Uint8Array(response.authenticatorData);
        const clientDataJSON = new Uint8Array(response.clientDataJSON);
        const rawId = new Uint8Array(newAssertion.rawId);
        const sig = new Uint8Array(response.signature);
        const assertionClientExtensions = newAssertion.getClientExtensionResults();

        return {
            id: newAssertion.id,
            rawId: this.b64enc(rawId),
            type: newAssertion.type,
            assertionClientExtensions: JSON.stringify(assertionClientExtensions),

            response: {
                clientDataJSON: this.b64RawEnc(clientDataJSON),
                signature: this.b64RawEnc(sig),
                authenticatorData: this.b64RawEnc(authData),
                userHandle: null,
            },
        };
    }

    render() {
        if (!this.deviceChallenge) {
            return this.renderChallengePicker();
        }
        switch (this.deviceChallenge.deviceClass) {
            case "static":
            case "totp":
                this.renderCodeInput();
                break;
            case "webauthn":
                this.renderWebauthn();
                break;
            default:
                break;
        }
    }

    renderChallengePicker() {
        const challenges = this.challenge.deviceChallenges.filter((challenge) =>
            challenge.deviceClass === "webauthn" && !this.checkWebAuthnSupport()
                ? undefined
                : challenge,
        );
        this.html(`<form id="picker-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                ${
                    challenges.length > 0
                        ? "<p>Select an authentication method.</p>"
                        : `
                    <p>No compatible authentication method available</p>
                    `
                }
                ${challenges
                    .map((challenge) => {
                        let label = undefined;
                        switch (challenge.deviceClass) {
                            case "static":
                                label = "Recovery keys";
                                break;
                            case "totp":
                                label = "Traditional authenticator";
                                break;
                            case "webauthn":
                                label = "Security key";
                                break;
                        }
                        if (!label) {
                            return "";
                        }
                        return `<div class="form-label-group my-3 has-validation">
                            <button id="${challenge.deviceClass}-${challenge.deviceUid}" class="btn btn-secondary w-100 py-2" type="button">
                                ${label}
                            </button>
                        </div>`;
                    })
                    .join("")}
            </form>`);
        this.challenge.deviceChallenges.forEach((challenge) => {
            $(`#picker-form button#${challenge.deviceClass}-${challenge.deviceUid}`).on(
                "click",
                () => {
                    this.deviceChallenge = challenge;
                    this.render();
                },
            );
        });
    }

    renderCodeInput() {
        this.html(`
            <form id="totp-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control ${this.error("code").length > 0 ? IS_INVALID : ""}" name="code" placeholder="Please enter your code" autocomplete="one-time-code">
                    ${this.renderInputError("code")}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);
        $("#totp-form input").trigger("focus");
        $("#totp-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target as HTMLFormElement);
            this.executor.submit(data);
        });
    }

    renderWebauthn() {
        this.html(`
            <form id="totp-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                <div class="d-flex justify-content-center">
                    <div class="spinner-border" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                </div>
            </form>
            `);
        navigator.credentials
            .get({
                publicKey: this.transformCredentialRequestOptions(
                    this.deviceChallenge?.challenge as PublicKeyCredentialRequestOptions,
                ),
            })
            .then((assertion) => {
                if (!assertion) {
                    throw new Error("No assertion");
                }
                try {
                    // we now have an authentication assertion! encode the byte arrays contained
                    // in the assertion data as strings for posting to the server
                    const transformedAssertionForServer = this.transformAssertionForServer(
                        assertion as PublicKeyCredential,
                    );

                    // post the assertion to the server for verification.
                    this.executor.submit({
                        webauthn: transformedAssertionForServer,
                    });
                } catch (err) {
                    throw new Error(`Error when validating assertion on server: ${err}`);
                }
            })
            .catch((error) => {
                console.warn(error);
                this.deviceChallenge = undefined;
                this.render();
            });
    }
}

const sfe = new SimpleFlowExecutor($("#flow-sfe-container")[0] as HTMLDivElement);
sfe.start();
