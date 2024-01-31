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
    DeviceChallengeTypesRequest,
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
                }
            `,
        ];
    }

    async submitDeviceChallenge(defaults?: Tout): Promise<boolean> {
        if (!this.deviceChallenge) {
            return false;
        }
        const formData = (await this.parseForm(
            defaults as unknown as DeviceChallengeResponseRequest,
        )) as unknown as DeviceChallengeResponseRequest;
        const selectedChallenge = this.deviceChallenge as unknown as DeviceChallengeTypesRequest;
        // @ts-expect-error
        formData.component = selectedChallenge.component;
        formData.uid = selectedChallenge.uid;
        const data: AuthenticatorValidationChallengeResponseRequest = {
            component: this.challenge.component,
            selectedChallenge: selectedChallenge,
            selectedChallengeResponse: formData,
        };
        return await this.host.submit(data);
    }
}
