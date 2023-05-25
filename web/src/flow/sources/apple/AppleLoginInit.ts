import "@goauthentik/elements/EmptyState";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AppleChallengeResponseRequest, AppleLoginChallenge } from "@goauthentik/api";

@customElement("ak-flow-source-oauth-apple")
export class AppleLoginInit extends BaseStage<AppleLoginChallenge, AppleChallengeResponseRequest> {
    @property({ type: Boolean })
    isModalShown = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle];
    }

    firstUpdated(): void {
        const appleAuth = document.createElement("script");
        appleAuth.src =
            "https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js";
        appleAuth.type = "text/javascript";
        appleAuth.onload = () => {
            AppleID.auth.init({
                clientId: this.challenge?.clientId,
                scope: this.challenge.scope,
                redirectURI: this.challenge.redirectUri,
                state: this.challenge.state,
                usePopup: false,
            });
            AppleID.auth.signIn();
            this.isModalShown = true;
        };
        document.head.append(appleAuth);
        //Listen for authorization success
        document.addEventListener("AppleIDSignInOnSuccess", () => {
            //handle successful response
        });
        //Listen for authorization failures
        document.addEventListener("AppleIDSignInOnFailure", (error) => {
            console.warn(error);
            this.isModalShown = false;
        });
    }

    render(): TemplateResult {
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${msg("Authenticating with Apple...")}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <ak-empty-state ?loading="${true}"> </ak-empty-state>
                    ${!this.isModalShown
                        ? html`<button
                              class="pf-c-button pf-m-primary pf-m-block"
                              @click=${() => {
                                  AppleID.auth.signIn();
                              }}
                          >
                              ${msg("Retry")}
                          </button>`
                        : html``}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
