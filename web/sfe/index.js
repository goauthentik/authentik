/* eslint-env jquery */

class SimpleFlowExecutor {
    challenge;
    flowSlug;
    container;

    constructor(container) {
        this.flowSlug = window.location.pathname.split("/")[3];
        this.container = container;
    }

    get apiURL() {
        return `/api/v3/flows/executor/${this.flowSlug}/?query=${encodeURIComponent(window.location.search.substring(1))}`;
    }

    start() {
        $.ajax({
            type: "GET",
            url: this.apiURL,
            success: (data) => {
                this.challenge = data;
                this.renderChallenge();
            },
        });
    }

    submit(data) {
        $("button[type=submit]").addClass("disabled")
            .html(`<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                <span role="status">Loading...</span>`);
        let object = data;
        if (data instanceof FormData) {
            object = {};
            data.forEach((value, key) => (object[key] = value));
        }
        $.ajax({
            type: "POST",
            url: this.apiURL,
            data: JSON.stringify(object),
            success: (data) => {
                this.challenge = data;
                this.renderChallenge();
            },
            contentType: "application/json",
            dataType: "json",
        });
    }

    renderChallenge() {
        switch (this.challenge.component) {
            case "ak-stage-identification":
                new IdentificationStage(this).render();
                return;
            case "ak-stage-password":
                new PasswordStage(this).render();
                return;
            case "xak-flow-redirect":
                new RedirectStage(this).render();
                return;
            case "ak-stage-autosubmit":
                new AutosubmitStage(this).render();
                return;
            case "ak-stage-authenticator-validate":
                new AuthenticatorValidateStage(this).render();
                return;
            default:
                this.container.innerText = "Unsupported stage: " + this.challenge.component;
                return;
        }
    }
}

class Stage {
    constructor(executor) {
        this.executor = executor;
    }

    error(fieldName) {
        if (!this.executor.challenge.response_errors) {
            return [];
        }
        return this.executor.challenge.response_errors[fieldName] || [];
    }

    renderInputError(fieldName) {
        return `${this.error(fieldName)
            .map((error) => {
                return `<div class="invalid-feedback">
                                ${error.string}
                            </div>`;
            })
            .join("")}`;
    }

    html(html) {
        this.executor.container.innerHTML = html;
    }

    render() {
        throw new Error("Abstract method");
    }
}

class IdentificationStage extends Stage {
    render() {
        this.html(`
            <form id="ident-form">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                ${
                    this.executor.challenge.application_pre
                        ? `<p>
                              Login to continue to ${this.executor.challenge.application_pre}.
                          </p>`
                        : ""
                }
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control" name="uid_field" placeholder="Email / Username">
                </div>
                ${
                    this.executor.challenge.password_fields
                        ? `<div class="form-label-group my-3 has-validation">
                                <input type="password" class="form-control ${this.error("password").length > 0 ? "is-invalid" : ""}" name="password" placeholder="Password">
                                ${this.renderInputError("password")}
                        </div>`
                        : ""
                }
                <button class="btn btn-primary w-100 py-2" type="submit">${this.executor.challenge.primary_action}</button>
            </form>`);
        $("#ident-form input[name=uid_field]").focus();
        $("#ident-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target);
            this.executor.submit(data);
        });
    }
}

class PasswordStage extends Stage {
    render() {
        this.html(`
            <form id="password-form">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                <div class="form-label-group my-3 has-validation">
                    <input type="password" autofocus class="form-control ${this.error("password").length > 0 ? "is-invalid" : ""}" name="password" placeholder="Password">
                    ${this.renderInputError("password")}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);
        $("#password-form input").focus();
        $("#password-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target);
            this.executor.submit(data);
        });
    }
}

class RedirectStage extends Stage {
    render() {
        window.location.assign(this.executor.challenge.to);
    }
}

class AutosubmitStage extends Stage {
    render() {
        this.html(`
            <form id="autosubmit-form" action="${this.executor.challenge.url}" method="POST">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                ${Object.entries(this.executor.challenge.attrs).map(([key, value]) => {
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

class AuthenticatorValidateStage extends Stage {
    deviceChallenge;

    b64enc(buf) {
        return base64js
            .fromByteArray(buf)
            .replace(/\+/g, "-")
            .replace(/\//g, "_")
            .replace(/=/g, "");
    }

    b64RawEnc(buf) {
        return base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_");
    }

    u8arr(input) {
        return Uint8Array.from(atob(input.replace(/_/g, "/").replace(/-/g, "+")), (c) =>
            c.charCodeAt(0),
        );
    }

    checkWebAuthnSupport() {
        if ("credentials" in navigator) {
            return;
        }
        if (window.location.protocol === "http:" && window.location.hostname !== "localhost") {
            throw new Error("WebAuthn requires this page to be accessed via HTTPS.");
        }
        throw new Error("WebAuthn not supported by browser.");
    }

    /**
     * Transforms items in the credentialCreateOptions generated on the server
     * into byte arrays expected by the navigator.credentials.create() call
     */
    transformCredentialCreateOptions(credentialCreateOptions, userId) {
        const user = credentialCreateOptions.user;
        // Because json can't contain raw bytes, the server base64-encodes the User ID
        // So to get the base64 encoded byte array, we first need to convert it to a regular
        // string, then a byte array, re-encode it and wrap that in an array.
        const stringId = decodeURIComponent(window.atob(userId));
        user.id = this.u8arr(this.b64enc(this.u8arr(stringId)));
        const challenge = this.u8arr(credentialCreateOptions.challenge.toString());

        const transformedCredentialCreateOptions = Object.assign({}, credentialCreateOptions, {
            challenge,
            user,
        });

        return transformedCredentialCreateOptions;
    }

    /**
     * Transforms the binary data in the credential into base64 strings
     * for posting to the server.
     * @param {PublicKeyCredential} newAssertion
     */
    transformNewAssertionForServer(newAssertion) {
        const attObj = new Uint8Array(newAssertion.response.attestationObject);
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

    transformCredentialRequestOptions(credentialRequestOptions) {
        const challenge = this.u8arr(credentialRequestOptions.challenge.toString());

        const allowCredentials = (credentialRequestOptions.allowCredentials || []).map(
            (credentialDescriptor) => {
                const id = this.u8arr(credentialDescriptor.id.toString());
                return Object.assign({}, credentialDescriptor, { id });
            },
        );

        const transformedCredentialRequestOptions = Object.assign({}, credentialRequestOptions, {
            challenge,
            allowCredentials,
        });

        return transformedCredentialRequestOptions;
    }

    /**
     * Encodes the binary data in the assertion into strings for posting to the server.
     * @param {PublicKeyCredential} newAssertion
     */
    transformAssertionForServer(newAssertion) {
        const response = newAssertion.response;
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
        switch (this.deviceChallenge.device_class) {
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
        this.html(`<form id="picker-form">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                <p>Select an authentication method.</p>
                ${this.executor.challenge.device_challenges
                    .map((challenge) => {
                        let label = undefined;
                        switch (challenge.device_class) {
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
                            <button id="${challenge.device_class}-${challenge.device_uid}" class="btn btn-secondary w-100 py-2" type="button">
                                ${label}
                            </button>
                        </div>`;
                    })
                    .join("")}
            </form>`);
        this.executor.challenge.device_challenges.forEach((challenge) => {
            $(`#picker-form button#${challenge.device_class}-${challenge.device_uid}`).on(
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
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control ${this.error("code").length > 0 ? "is-invalid" : ""}" name="code" placeholder="Please enter your code" autocomplete="one-time-code">
                    ${this.renderInputError("code")}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);
        $("#totp-form input").focus();
        $("#totp-form").on("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target);
            this.executor.submit(data);
        });
    }

    async renderWebauthn() {
        this.html(`
            <form id="totp-form">
                <img class="mb-4 brand-icon" src="${window.authentik.brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.executor.challenge.flow_info.title}</h1>
                <div class="d-flex justify-content-center">
                    <div class="spinner-border" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                </div>
            </form>
            `);
        this.checkWebAuthnSupport();
        let assertion;
        try {
            assertion = await navigator.credentials.get({
                publicKey: this.transformCredentialRequestOptions(this.deviceChallenge.challenge),
            });
            if (!assertion) {
                throw new Error("Assertions is empty");
            }
        } catch (err) {
            throw new Error(`Error when creating credential: ${err}`);
        }

        // we now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server
        const transformedAssertionForServer = this.transformAssertionForServer(assertion);

        // post the assertion to the server for verification.
        try {
            this.executor.submit({
                webauthn: transformedAssertionForServer,
            });
        } catch (err) {
            throw new Error(`Error when validating assertion on server: ${err}`);
        }
    }
}

const sfe = new SimpleFlowExecutor($("#flow-sfe-container")[0]);
sfe.start();
