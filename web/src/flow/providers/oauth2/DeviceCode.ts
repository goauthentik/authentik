import "#elements/forms/FormElement";
import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import {
    OAuthDeviceCodeChallenge,
    OAuthDeviceCodeChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-flow-provider-oauth2-code")
export class OAuth2DeviceCode extends BaseStage<
    OAuthDeviceCodeChallenge,
    OAuthDeviceCodeChallengeResponseRequest
> {
    public static override styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        PFButton,
    ];

    public override render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
                <form
                    class="pf-c-form"
                    @submit=${this.submitForm}
                >
                    <input
                        type="text"
                        name="code"
                        inputmode="numeric"
                        pattern="[0-9]*"
                        placeholder="${msg("Please enter your Code")}"
                        autofocus=""
                        autocomplete="off"
                        class="pf-c-form-control"
                        value=""
                        required
                    />
                </ak-form-element>

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
        "ak-flow-provider-oauth2-code": OAuth2DeviceCode;
    }
}
