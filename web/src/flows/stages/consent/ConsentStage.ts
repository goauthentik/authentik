import { t } from "@lingui/macro";
import { CSSResult, customElement, html, TemplateResult } from "lit-element";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { BaseStage } from "../base";
import "../../../elements/EmptyState";
import "../../FormStatic";
import { ConsentChallenge, ConsentChallengeResponseRequest } from "authentik-api";
import { ifDefined } from "lit-html/directives/if-defined";


@customElement("ak-stage-consent")
export class ConsentStage extends BaseStage<ConsentChallenge, ConsentChallengeResponseRequest> {

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${t`Loading`}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.flowInfo?.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e: Event) => { this.submitForm(e); }}>
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}>
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}">${t`Not you?`}</a>
                        </div>
                    </ak-form-static>
                    <div class="pf-c-form__group">
                        <p id="header-text">
                            ${this.challenge.headerText}
                        </p>
                        ${this.challenge.permissions.length > 0 ? html`
                            <p>${t`Application requires following permissions`}</p>
                            <ul class="pf-c-list" id="permmissions">
                                ${this.challenge.permissions.map((permission) => {
                                    return html`<li data-permission-code="${permission.id}">${permission.name}</li>`;
                                })}
                            </ul>
                        ` : html``}
                    </div>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${t`Continue`}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
