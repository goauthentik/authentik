/**
 * @import { AuthenticatorValidationChallenge, DeviceChallenge } from "@goauthentik/api";
 * @import { FlowExecutor } from './Stage.js';
 */
import {
    isWebAuthnSupported,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "@goauthentik/web/authentication";
import $ from "jquery";

import { Stage } from "./Stage.js";
import { ak } from "./utils.js";

//@ts-check

/**
 * @template {AuthenticatorValidationChallenge} T
 * @extends {Stage<T>}
 */
export class AuthenticatorValidateStage extends Stage {
    /**
     * @param {FlowExecutor} executor - The executor for this stage
     * @param {T} challenge - The challenge for this stage
     */
    constructor(executor, challenge) {
        super(executor, challenge);

        /**
         * @type {DeviceChallenge | null}
         */
        this.deviceChallenge = null;
    }

    render() {
        if (!this.deviceChallenge) {
            this.renderChallengePicker();
            return;
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

    /**
     * @private
     */
    renderChallengePicker() {
        const challenges = this.challenge.deviceChallenges.filter((challenge) =>
            challenge.deviceClass === "webauthn" && !isWebAuthnSupported() ? undefined : challenge,
        );

        this.html(/* html */ `<form id="picker-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                ${
                    challenges.length > 0
                        ? /* html */ `<p>Select an authentication method.</p>`
                        : /* html */ `<p>No compatible authentication method available</p>`
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

                        if (!label) return "";

                        return /* html */ `<div class="form-label-group my-3 has-validation">
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

    /**
     * @private
     */
    renderCodeInput() {
        this.html(/* html */ `
            <form id="totp-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control ${this.error("code").length > 0 ? "is-invalid" : ""}" name="code" placeholder="Please enter your code" autocomplete="one-time-code">
                    ${this.renderInputError("code")}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);

        $("#totp-form input").trigger("focus");

        $("#totp-form").on("submit", (ev) => {
            ev.preventDefault();

            const target = /** @type {HTMLFormElement} */ (ev.target);

            const data = new FormData(target);
            this.executor.submit(data);
        });
    }

    /**
     * @private
     */
    renderWebauthn() {
        this.html(/* html */ `
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

        const challenge = /** @type {PublicKeyCredentialRequestOptions} */ (
            this.deviceChallenge?.challenge
        );

        navigator.credentials
            .get({
                publicKey: transformCredentialRequestOptions(challenge),
            })
            .then((credential) => {
                if (!credential) {
                    throw new Error("No assertion");
                }

                if (credential.type !== "public-key") {
                    throw new Error("Invalid assertion type");
                }

                try {
                    // We now have an authentication assertion!
                    // Encode the byte arrays contained in the assertion data as strings
                    // for posting to the server.
                    const transformedAssertionForServer = transformAssertionForServer(
                        /** @type {PublicKeyCredential} */ (credential),
                    );

                    // Post the assertion to the server for verification.
                    this.executor.submit({
                        webauthn: transformedAssertionForServer,
                    });
                } catch (err) {
                    throw new Error(`Error when validating assertion on server: ${err}`);
                }
            })
            .catch((error) => {
                console.warn(error);

                this.deviceChallenge = null;
                this.render();
            });
    }
}
