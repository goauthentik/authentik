import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { FlowChallengeResponseRequest, RedirectChallenge } from "@goauthentik/api";

import { BaseStage } from "./base";

@customElement("ak-stage-redirect")
export class RedirectStage extends BaseStage<RedirectChallenge, FlowChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFButton, PFFormControl, PFTitle, AKGlobal];
    }

    renderURL(): string {
        if (!this.challenge.to.includes("://")) {
            return window.location.origin + this.challenge.to;
        }
        return this.challenge.to;
    }

    render(): TemplateResult {
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${t`Redirect`}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form method="POST" class="pf-c-form">
                    <div class="pf-c-form__group">
                        <p>${t`You're about to be redirect to the following URL.`}</p>
                        <pre>${this.renderURL()}</pre>
                    </div>
                    <div class="pf-c-form__group pf-m-action">
                        <a
                            type="submit"
                            class="pf-c-button pf-m-primary pf-m-block"
                            href=${this.challenge.to}
                        >
                            ${t`Follow redirect`}
                        </a>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer> `;
    }
}
