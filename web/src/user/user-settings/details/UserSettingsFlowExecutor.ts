import { t } from "@lingui/macro";

import { LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import {
    ChallengeChoices,
    ChallengeTypes,
    FlowChallengeResponseRequest,
    FlowsApi,
    ShellChallenge,
} from "@goauthentik/api";

import { DEFAULT_CONFIG, tenant } from "../../../api/Config";
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

    submit(payload?: FlowChallengeResponseRequest): Promise<boolean> {
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
            this.loading = true;
            new FlowsApi(DEFAULT_CONFIG)
                .flowsExecutorGet({
                    flowSlug: this.flowSlug,
                    query: window.location.search.substring(1),
                })
                .then((challenge) => {
                    this.challenge = challenge;
                })
                .catch((e: Error | Response) => {
                    // Catch JSON or Update errors
                    this.errorMessage(e);
                })
                .finally(() => {
                    this.loading = false;
                });
        });
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

    renderChallenge(): TemplateResult {
        if (!this.challenge) {
            return html``;
        }
        switch (this.challenge.type) {
            case ChallengeChoices.Redirect:
                return html`<a href="" class="pf-c-button">${"Edit settings"}</a>`;
            case ChallengeChoices.Shell:
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case ChallengeChoices.Native:
                switch (this.challenge.component) {
                    case "ak-stage-prompt":
                        return html`<ak-user-settings-stage-prompt
                            .host=${this as StageHost}
                            .challenge=${this.challenge}
                        ></ak-user-settings-stage-prompt>`;
                    default:
                        console.log(
                            `authentik/user/flows: unsupported stage type ${this.challenge.component}`,
                        );
                        return html`
                            <a href="/if/flow/${this.flowSlug}" class="pf-c-button">
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

    render(): TemplateResult {
        if (!this.flowSlug) {
            return html` <p>${t`No settings flow configured.`}/p></p> `;
        }
        if (!this.challenge) {
            return html`<ak-empty-state ?loading=${true} header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`
            ${this.loading ? html`<ak-loading-overlay></ak-loading-overlay>` : html``}
            ${this.renderChallenge()}
        `;
    }
}
