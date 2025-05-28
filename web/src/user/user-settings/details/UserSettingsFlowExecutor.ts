import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { globalAK } from "#common/global";
import { MessageLevel } from "#common/messages";
import { refreshMe } from "#common/users";
import { AKElement } from "#elements/Base";
import { showMessage } from "#elements/messages/MessageContainer";
import { WithBrandConfig } from "#elements/mixins/branding";
import { StageHost } from "#flow/stages/base";
import "#user/user-settings/details/stages/prompt/PromptStage";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    ChallengeTypes,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowsApi,
    RedirectChallenge,
    ShellChallenge,
} from "@goauthentik/api";

@customElement("ak-user-settings-flow-executor")
export class UserSettingsFlowExecutor
    extends WithBrandConfig(AKElement, true)
    implements StageHost
{
    @property()
    flowSlug?: string;

    private _challenge?: ChallengeTypes;

    @property({ attribute: false })
    set challenge(value: ChallengeTypes | undefined) {
        this._challenge = value;
        this.requestUpdate();
    }

    get challenge(): ChallengeTypes | undefined {
        return this._challenge;
    }

    @property({ type: Boolean })
    loading = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFPage, PFButton, PFContent];
    }

    submit(payload?: FlowChallengeResponseRequest): Promise<boolean> {
        if (!payload) return Promise.reject();
        if (!this.challenge) return Promise.reject();
        // @ts-ignore
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

    updated(changedProperties: PropertyValues<this>): void {
        if (changedProperties.has("brand") && this.brand) {
            this.flowSlug = this.brand.flowUserSettings;

            if (!this.flowSlug) return;

            this.nextChallenge();
        }
    }

    async nextChallenge(): Promise<void> {
        this.loading = true;
        try {
            const challenge = await new FlowsApi(DEFAULT_CONFIG).flowsExecutorGet({
                flowSlug: this.flowSlug || "",
                query: window.location.search.substring(1),
            });
            this.challenge = challenge;
        } catch (e: unknown) {
            // Catch JSON or Update errors
            this.errorMessage(e as Error | Response);
        } finally {
            this.loading = false;
        }
    }

    async errorMessage(error: APIError): Promise<void> {
        const challenge: FlowErrorChallenge = {
            component: "ak-stage-flow-error",
            error: pluckErrorDetail(error),
            requestId: "",
        };

        this.challenge = challenge as ChallengeTypes;
    }

    globalRefresh(): void {
        refreshMe().then(() => {
            this.dispatchEvent(
                new CustomEvent(EVENT_REFRESH, {
                    bubbles: true,
                    composed: true,
                }),
            );
            try {
                document.querySelectorAll("ak-interface-user").forEach((int) => {
                    (int as AKElement).requestUpdate();
                });
            } catch {
                console.debug("authentik/user/flows: failed to find interface to refresh");
            }
        });
    }

    renderChallenge(): TemplateResult {
        if (!this.challenge) {
            return html``;
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
                this.loading = true;
                console.debug("authentik/user/flows: redirect to '/', restarting flow.");
                this.nextChallenge();
                this.globalRefresh();
                showMessage({
                    level: MessageLevel.success,
                    message: msg("Successfully updated details"),
                });
                return html`<ak-empty-state loading header=${msg("Loading")}> </ak-empty-state>`;
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
            return html`<ak-empty-state loading header=${msg("Loading")}> </ak-empty-state>`;
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
