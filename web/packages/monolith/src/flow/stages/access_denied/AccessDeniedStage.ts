import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AccessDeniedChallenge, FlowChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-access-denied-icon")
export class AccessDeniedIcon extends AKElement {
    @property()
    errorMessage?: string;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFTitle,
            css`
                .big-icon {
                    display: flex;
                    width: 100%;
                    justify-content: center;
                    height: 5rem;
                }
                .big-icon i {
                    font-size: 3rem;
                }
                .reason {
                    margin-bottom: 1rem;
                    text-align: center;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html` <div class="pf-c-form__group">
            <p class="big-icon">
                <i class="pf-icon pf-icon-error-circle-o"></i>
            </p>
            <h3 class="pf-c-title pf-m-3xl reason">${msg("Request has been denied.")}</h3>
            ${this.errorMessage
                ? html`<hr />
                      <p>${this.errorMessage}</p>`
                : html``}
        </div>`;
    }
}

@customElement("ak-stage-access-denied")
export class AccessDeniedStage extends BaseStage<
    AccessDeniedChallenge,
    FlowChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFList, PFFormControl, PFTitle];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${msg("Not you?")}</a
                            >
                        </div>
                    </ak-form-static>
                    <ak-stage-access-denied-icon
                        errorMessage=${ifDefined(this.challenge.errorMessage)}
                    >
                    </ak-stage-access-denied-icon>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
