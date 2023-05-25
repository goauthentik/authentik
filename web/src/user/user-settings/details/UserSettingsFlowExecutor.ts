import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { MessageLevel } from "@goauthentik/common/messages";
import { refreshMe } from "@goauthentik/common/users";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import { StageHost } from "@goauthentik/flow/stages/base";
import "@goauthentik/user/user-settings/details/stages/prompt/PromptStage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    ChallengeChoices,
    ChallengeTypes,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowsApi,
    RedirectChallenge,
    ResponseError,
    ShellChallenge,
} from "@goauthentik/api";

@customElement("ak-user-settings-flow-executor")
export class UserSettingsFlowExecutor extends AKElement implements StageHost {
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
                if (this.challenge.responseErrors) {
                    return false;
                }
                return true;
            })
            .catch((e: Error | ResponseError) => {
                this.errorMessage(e);
                return false;
            })
            .finally(() => {
                this.loading = false;
                return false;
            });
    }

    firstUpdated(): void {
        const tenant = rootInterface()?.tenant;
        this.flowSlug = tenant?.flowUserSettings;
        if (!this.flowSlug) {
            return;
        }
        this.nextChallenge();
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

    async errorMessage(error: Error | Response): Promise<void> {
        let body = "";
        if (error instanceof Error) {
            body = error.message;
        }
        const challenge: FlowErrorChallenge = {
            type: ChallengeChoices.Native,
            component: "ak-stage-flow-error",
            error: body,
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
        switch (this.challenge.type) {
            case ChallengeChoices.Redirect:
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
                this.firstUpdated();
                this.globalRefresh();
                showMessage({
                    level: MessageLevel.success,
                    message: msg("Successfully updated details"),
                });
                return html`<ak-empty-state ?loading=${true} header=${msg("Loading")}>
                </ak-empty-state>`;
            case ChallengeChoices.Shell:
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case ChallengeChoices.Native:
                switch (this.challenge.component) {
                    case "ak-stage-prompt":
                        return html`<ak-user-stage-prompt
                            .host=${this as StageHost}
                            .challenge=${this.challenge}
                        ></ak-user-stage-prompt>`;
                    default:
                        console.debug(
                            `authentik/user/flows: unsupported stage type ${this.challenge.component}`,
                        );
                        return html`
                            <a href="/if/flow/${this.flowSlug}" class="pf-c-button pf-m-primary">
                                ${msg("Open settings")}
                            </a>
                        `;
                }
            default:
                console.debug(`authentik/user/flows: unexpected data type ${this.challenge.type}`);
                break;
        }
        return html``;
    }

    renderChallengeWrapper(): TemplateResult {
        if (!this.flowSlug) {
            return html`<p>${msg("No settings flow configured.")}</p> `;
        }
        if (!this.challenge || this.loading) {
            return html`<ak-empty-state ?loading=${true} header=${msg("Loading")}>
            </ak-empty-state>`;
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
