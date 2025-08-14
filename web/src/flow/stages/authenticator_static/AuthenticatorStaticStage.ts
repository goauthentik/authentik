import "#elements/forms/FormElement";
import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import {
    downloadCodes,
    printCodes,
} from "#user/user-settings/authenticator_static/UserSettingsAuthenticatorStaticModal";

import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorStaticChallenge,
    AuthenticatorStaticChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-authenticator-static")
export class AuthenticatorStaticStage extends BaseStage<
    AuthenticatorStaticChallenge,
    AuthenticatorStaticChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        PFButton,
        PFFlex,
        css`
            /* Static OTP Tokens */
            ul {
                list-style: circle;
                columns: 2;
                -webkit-columns: 2;
                -moz-columns: 2;
                column-width: 1em;
                margin-left: var(--pf-global--spacer--xs);
            }
            ul li {
                font-size: var(--pf-global--FontSize--2xl);
                margin: 0 2rem;
            }
            .pf-l-flex {
                margin-bottom: var(--pf-global--spacer--md);
            }
        `,
    ];

    downloadCodes(): void {
        downloadCodes(this.challenge.codes);
    }

    printCodes(): void {
        printCodes(this.challenge.codes);
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
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
                <ak-form-element label="" class="pf-c-form__group">
                    <ul>
                        ${this.challenge.codes.map((token) => {
                            return html`<li class="pf-m-monospace">${token}</li>`;
                        })}
                    </ul>
                </ak-form-element>
                <p class="pf-u-text-align-center">${msg("Make sure to keep these tokens in a safe place.")}</p>

                <div class="pf-l-flex pf-m-justify-content-center pf-m-align-items-center pf-m-gap-md pf-u-my-xl">
                    <button 
                        type="button" 
                        class="pf-c-button pf-m-primary pf-m-block"
                        style="max-width: 200px;"
                        @click=${this.downloadCodes}
                    >
                        <i class="fas fa-download pf-u-mr-xs" aria-hidden="true"></i>
                        ${msg("Download codes")}
                    </button>
                    <button 
                        type="button" 
                        class="pf-c-button pf-m-secondary pf-m-block"
                        style="max-width: 200px;"
                        @click=${this.printCodes}
                    >
                        <i class="fas fa-print pf-u-mr-xs" aria-hidden="true"></i>
                        ${msg("Print codes")}
                    </button>
                </div>

                <div class="pf-c-form__group pf-m-action">
                    <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                        ${msg("Continue")}
                    </button>
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-static": AuthenticatorStaticStage;
    }
}
