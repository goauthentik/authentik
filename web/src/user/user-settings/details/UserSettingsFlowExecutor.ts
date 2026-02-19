import "#user/user-settings/details/stages/prompt/PromptStage";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { globalAK } from "#common/global";
import { MessageLevel } from "#common/messages";

import { AKElement } from "#elements/Base";
import { showMessage } from "#elements/messages/MessageContainer";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithSession } from "#elements/mixins/session";
import { SlottedTemplateResult } from "#elements/types";

import type { StageHost } from "#flow/types";

import {
    ChallengeTypes,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowsApi,
    RedirectChallenge,
    ShellChallenge,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-user-settings-flow-executor")
export class UserSettingsFlowExecutor
    extends WithBrandConfig(WithSession(AKElement), true)
    implements StageHost
{
    @property()
    flowSlug = this.brand?.flowUserSettings;

    #challenge: ChallengeTypes | null = null;

    @property({ attribute: false })
    set challenge(value: ChallengeTypes | null) {
        const previousValue = this.#challenge;

        this.#challenge = value;

        this.requestUpdate("challenge", previousValue);
    }

    get challenge(): ChallengeTypes | null {
        return this.#challenge;
    }

    @property({ type: Boolean })
    loading = false;

    static styles: CSSResult[] = [PFCard, PFPage, PFButton, PFContent];

    submit(payload?: FlowChallengeResponseRequest): Promise<boolean> {
        if (!payload) return Promise.reject();
        if (!this.challenge) return Promise.reject();
        // @ts-expect-error Component is too generic for Typescript here.
        payload.component = this.challenge.component;
        this.loading = true;
        return new FlowsApi(DEFAULT_CONFIG)
            .flowsExecutorSolve({
                flowSlug: this.flowSlug || "",
                query: window.location.search.substring(1),
                flowChallengeResponseRequest: payload,
            })
            .then((data) => {
                this.challenge = data;
                delete this.challenge.flowInfo;
                return !this.challenge.responseErrors;
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);

                this.errorMessage(parsedError);

                return false;
            })
            .finally(() => {
                this.loading = false;
                return false;
            });
    }

    firstUpdated() {
        if (this.flowSlug) {
            this.nextChallenge();
        }
    }

    updated(): void {
        if (!this.flowSlug && this.brand?.flowUserSettings) {
            this.flowSlug = this.brand.flowUserSettings;
            this.nextChallenge();
        }
    }

    async nextChallenge(): Promise<void> {
        this.loading = true;

        return new FlowsApi(DEFAULT_CONFIG)
            .flowsExecutorGet({
                flowSlug: this.flowSlug || "",
                query: window.location.search.substring(1),
            })
            .then((challenge) => {
                delete challenge.flowInfo;
                this.challenge = challenge;
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);
                this.errorMessage(parsedError);
            })
            .finally(() => {
                this.loading = false;
            });
    }

    async errorMessage(error: APIError): Promise<void> {
        const challenge: FlowErrorChallenge = {
            component: "ak-stage-flow-error",
            error: pluckErrorDetail(error),
            requestId: "",
        };

        this.challenge = challenge as ChallengeTypes;
    }

    #performSessionChallenge = () => {
        console.debug("authentik/user/flows: redirect to '/', restarting flow.");

        return this.nextChallenge().then(() => {
            showMessage({
                level: MessageLevel.success,
                message: msg("Successfully updated details"),
            });

            this.refreshSession();
        });
    };

    renderChallenge(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }
        switch (this.challenge.component) {
            case "ak-stage-prompt":
                return html`<ak-user-stage-prompt
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-user-stage-prompt>`;
            case "xak-flow-shell":
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case "xak-flow-redirect":
                if ((this.challenge as RedirectChallenge).to !== "/") {
                    return html`<a
                        href="${(this.challenge as RedirectChallenge).to}"
                        class="pf-c-button pf-m-primary"
                        >${"Edit settings"}</a
                    >`;
                }

                // Flow has finished, so let's load while in the background we can restart the flow
                this.#performSessionChallenge();
                return html`<ak-empty-state default-label></ak-empty-state>`;
            default:
                console.debug(
                    `authentik/user/flows: unsupported stage type ${this.challenge.component}`,
                );
                return html`
                    <a
                        href="${globalAK().api.base}if/flow/${this.flowSlug}/"
                        class="pf-c-button pf-m-primary"
                    >
                        ${msg("Open settings")}
                    </a>
                `;
        }
    }

    renderChallengeWrapper(): TemplateResult {
        if (!this.flowSlug) {
            return html`<p>${msg("No settings flow configured.")}</p> `;
        }
        if (!this.challenge || this.loading) {
            return html`<ak-empty-state default-label></ak-empty-state>`;
        }
        return html` ${this.renderChallenge()} `;
    }

    render(): TemplateResult {
        return html` <div class="pf-c-card">
            <div class="pf-c-card__title">${msg("Update details")}</div>
            <div class="pf-c-card__body">${this.renderChallengeWrapper()}</div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-flow-executor": UserSettingsFlowExecutor;
    }
}
