import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    ChallengeChoices,
    ChallengeTypes,
    CurrentTenant,
    FlowChallengeResponseRequest,
    FlowsApi,
    RedirectChallenge,
    ShellChallenge,
} from "@goauthentik/api";

import { DEFAULT_CONFIG, tenant } from "../../../api/Config";
import { refreshMe } from "../../../api/Users";
import { EVENT_REFRESH } from "../../../constants";
import { MessageLevel } from "../../../elements/messages/Message";
import { showMessage } from "../../../elements/messages/MessageContainer";
import { StageHost } from "../../../flows/stages/base";
import "./stages/prompt/PromptStage";

@customElement("ak-user-settings-flow-executor")
export class UserSettingsFlowExecutor extends LitElement implements StageHost {
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

    @property({ attribute: false })
    tenant!: CurrentTenant;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFPage, PFButton, PFContent, AKGlobal];
    }

    constructor() {
        super();
        tenant().then((tenant) => (this.tenant = tenant));
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
            .catch((e: Error | Response) => {
                this.errorMessage(e);
                return false;
            })
            .finally(() => {
                this.loading = false;
                return false;
            });
    }

    firstUpdated(): void {
        tenant().then((tenant) => {
            this.flowSlug = tenant.flowUserSettings;
            if (!this.flowSlug) {
                return;
            }
            new FlowsApi(DEFAULT_CONFIG)
                .flowsInstancesExecuteRetrieve({
                    slug: this.flowSlug || "",
                })
                .then(() => {
                    this.nextChallenge();
                });
        });
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
        this.challenge = {
            type: ChallengeChoices.Shell,
            body: `<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${t`Whoops!`}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <h3>${t`Something went wrong! Please try again later.`}</h3>
                <pre class="ak-exception">${body}</pre>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                    <li class="pf-c-login__main-footer-links-item">
                        <a class="pf-c-button pf-m-primary pf-m-block" href="/">
                            ${t`Return`}
                        </a>
                    </li>
                </ul>
            </footer>`,
        } as ChallengeTypes;
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
                    (int as LitElement).requestUpdate();
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
                    message: t`Successfully updated details`,
                });
                return html`<ak-empty-state ?loading=${true} header=${t`Loading`}>
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
                        console.log(
                            `authentik/user/flows: unsupported stage type ${this.challenge.component}`,
                        );
                        return html`
                            <a href="/if/flow/${this.flowSlug}" class="pf-c-button pf-m-primary">
                                ${t`Open settings`}
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
            return html`<p>${t`No settings flow configured.`}</p> `;
        }
        if (!this.challenge || this.loading) {
            return html`<ak-empty-state ?loading=${true} header=${t`Loading`}> </ak-empty-state>`;
        }
        return html` ${this.renderChallenge()} `;
    }

    render(): TemplateResult {
        return html` <div class="pf-c-card">
            <div class="pf-c-card__title">${t`Update details`}</div>
            <div class="pf-c-card__body">${this.renderChallengeWrapper()}</div>
        </div>`;
    }
}
