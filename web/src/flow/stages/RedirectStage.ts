import "@goauthentik/flow/components/ak-flow-card.js";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { FlowChallengeResponseRequest, RedirectChallenge } from "@goauthentik/api";

@customElement("ak-stage-redirect")
export class RedirectStage extends BaseStage<RedirectChallenge, FlowChallengeResponseRequest> {
    @property({ type: Boolean })
    promptUser = false;

    @state()
    startedRedirect = false;

    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFButton,
        PFFormControl,
        PFTitle,
        css`
            code {
                word-break: break-all;
            }
        `,
    ];

    getURL(): string {
        return new URL(this.challenge.to, document.baseURI).toString();
    }

    firstUpdated(): void {
        if (this.promptUser) {
            document.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter") {
                    this.redirect();
                }
            });
            return;
        }
        this.redirect();
    }

    redirect() {
        console.debug(
            "authentik/stages/redirect: redirecting to url from server",
            this.challenge.to,
        );
        window.location.assign(this.challenge.to);
        this.startedRedirect = true;
    }

    renderLoading(): TemplateResult {
        const url = new URL(this.getURL());
        // If the protocol isn't http or https assume a custom protocol, that has an OS-level
        // handler, which the browser will show a popup for.
        // As this wouldn't really be a redirect, show a message that the page can be closed
        // and try to close it ourselves
        if (!url.protocol.startsWith("http")) {
            return html`<ak-flow-card .challenge=${this.challenge}>
                <ak-empty-state icon="fas fa-check"
                    ><span>${msg("You may close this page now.")}</span>
                </ak-empty-state>
            </ak-flow-card>`;
        }
        return html`<ak-flow-card .challenge=${this.challenge} loading></ak-flow-card>`;
    }

    render(): TemplateResult {
        if (this.startedRedirect || !this.promptUser) {
            return this.renderLoading();
        }
        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Redirect")}</span>
            <form class="pf-c-form">
                <div class="pf-c-form__group">
                    <p>${msg("You're about to be redirect to the following URL.")}</p>
                    <code>${this.getURL()}</code>
                </div>
                <div class="pf-c-form__group pf-m-action">
                    <a
                        type="submit"
                        class="pf-c-button pf-m-primary pf-m-block"
                        href=${this.challenge.to}
                        @click=${() => {
                            this.startedRedirect = true;
                        }}
                    >
                        ${msg("Follow redirect")}
                    </a>
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-redirect": RedirectStage;
    }
}
