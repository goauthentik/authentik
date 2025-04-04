/**
 * @import { ChallengeTypes } from "@goauthentik/api";
 * @import { FlowExecutor } from './Stage.js';
 */
import $ from "jquery";

import { ChallengeTypesFromJSON } from "@goauthentik/api";

import { AuthenticatorValidateStage } from "./AuthenticatorValidateStage.js";
import { AutosubmitStage } from "./AutosubmitStage.js";
import { IdentificationStage } from "./IdentificationStage.js";
import { PasswordStage } from "./PasswordStage.js";
import { RedirectStage } from "./RedirectStage.js";
import { ak } from "./utils.js";

/**
 * Simple Flow Executor lifecycle.
 *
 * @implements {FlowExecutor}
 */
export class SimpleFlowExecutor {
    /**
     *
     * @param {HTMLDivElement} container
     */
    constructor(container) {
        /**
         * @type {ChallengeTypes | null} The current challenge.
         */
        this.challenge = null;
        /**
         * @type {string} The flow slug.
         */
        this.flowSlug = window.location.pathname.split("/")[3] || "";
        /**
         * @type {HTMLDivElement} The container element for the flow executor.
         */
        this.container = container;
    }

    get apiURL() {
        return `${ak().api.base}api/v3/flows/executor/${this.flowSlug}/?query=${encodeURIComponent(window.location.search.substring(1))}`;
    }

    start() {
        $.ajax({
            type: "GET",
            url: this.apiURL,
            success: (data) => {
                this.challenge = ChallengeTypesFromJSON(data);

                this.renderChallenge();
            },
        });
    }

    /**
     * Submits the form data.
     * @param {Record<string, unknown> | FormData} payload
     */
    submit(payload) {
        $("button[type=submit]").addClass("disabled")
            .html(`<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                <span role="status">Loading...</span>`);
        /**
         * @type {Record<string, unknown>}
         */
        let finalData;

        if (payload instanceof FormData) {
            finalData = {};

            payload.forEach((value, key) => {
                finalData[key] = value;
            });
        } else {
            finalData = payload;
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

    /**
     * @returns {void}
     */
    renderChallenge() {
        switch (this.challenge?.component) {
            case "ak-stage-identification":
                return new IdentificationStage(this, this.challenge).render();
            case "ak-stage-password":
                return new PasswordStage(this, this.challenge).render();
            case "xak-flow-redirect":
                return new RedirectStage(this, this.challenge).render();
            case "ak-stage-autosubmit":
                return new AutosubmitStage(this, this.challenge).render();
            case "ak-stage-authenticator-validate":
                return new AuthenticatorValidateStage(this, this.challenge).render();
            default:
                this.container.innerText = `Unsupported stage: ${this.challenge?.component}`;
                return;
        }
    }
}
