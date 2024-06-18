import { AuthenticatorValidateStage } from "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage";
import { BaseStage, FlowInfoChallenge, PendingUserChallenge } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { DeviceChallenge } from "@goauthentik/api";

export class BaseDeviceStage<
    Tin extends FlowInfoChallenge & PendingUserChallenge,
    Tout,
> extends BaseStage<Tin, Tout> {
    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    showBackButton = false;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFForm,
            PFFormControl,
            PFTitle,
            PFButton,
            css`
                .pf-c-form__group.pf-m-action {
                    display: flex;
                    gap: 16px;
                    margin-top: 0;
                    margin-bottom: calc(var(--pf-c-form__group--m-action--MarginTop) / 2);
                    flex-direction: column;
                }
            `,
        ];
    }

    submit(payload: Tin): Promise<boolean> {
        return this.host?.submit(payload) || Promise.resolve();
    }

    renderReturnToDevicePicker(): TemplateResult {
        if (!this.showBackButton) {
            return html``;
        }
        return html`<button
            class="pf-c-button pf-m-secondary pf-m-block"
            @click=${() => {
                if (!this.host) return;
                (this.host as AuthenticatorValidateStage).selectedDeviceChallenge = undefined;
            }}
        >
            ${msg("Return to device picker")}
        </button>`;
    }
}
