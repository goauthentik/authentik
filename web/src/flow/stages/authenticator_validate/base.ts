import { AuthenticatorValidateStage } from "@goauthentik/app/flow/stages/authenticator_validate/AuthenticatorValidateStage";
import { BaseStage } from "@goauthentik/app/flow/stages/base";

import { CSSResult, css } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallengeResponseRequest,
    DeviceChallengeTypes,
} from "@goauthentik/api";

export class BaseDeviceStage<Tin, Tout> extends BaseStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    deviceChallenge?: Tin;

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
                    margin-bottom: var(--pf-c-form__group--m-action--MarginTop);
                }
            `,
        ];
    }

    async returnToDevicePicker(): Promise<void> {
        const host = this.host as AuthenticatorValidateStage;
        host.selectedDeviceChallenge = undefined;
    }

    async submitDeviceChallenge(defaults?: Tout, loading: boolean = true): Promise<boolean> {
        if (!this.deviceChallenge) {
            return false;
        }
        const formData = (await this.parseForm(
            defaults as unknown as DeviceChallengeResponseRequest,
        )) as unknown as DeviceChallengeResponseRequest;
        const selectedChallenge = this.deviceChallenge as unknown as DeviceChallengeTypes;
        formData.component = selectedChallenge.component;
        formData.uid = selectedChallenge.uid;
        const data: AuthenticatorValidationChallengeResponseRequest = {
            component: this.challenge.component,
            selectedChallengeUid: selectedChallenge.uid,
            selectedChallengeResponse: formData,
        };
        return await this.host.submit(data, loading);
    }
}
