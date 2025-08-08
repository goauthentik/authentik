import { AuthenticatorValidateStage } from "#flow/stages/authenticator_validate/AuthenticatorValidateStage";
import { BaseStage, FlowInfoChallenge, PendingUserChallenge } from "#flow/stages/base";

import { DeviceChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export class BaseDeviceStage<
    Tin extends FlowInfoChallenge & PendingUserChallenge,
    Tout,
> extends BaseStage<Tin, Tout> {
    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    showBackButton = false;

    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFFormControl,
        PFInputGroup,
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

    submit(payload: Tin): Promise<boolean> {
        return this.host?.submit(payload) || Promise.resolve();
    }

    renderReturnToDevicePicker() {
        if (!this.showBackButton) {
            return nothing;
        }
        return html`<button
            class="pf-c-button pf-m-secondary pf-m-block"
            @click=${() => {
                if (!this.host) return;
                (this.host as AuthenticatorValidateStage).selectedDeviceChallenge = undefined;
            }}
        >
            ${msg("Select another authentication method")}
        </button>`;
    }
}
