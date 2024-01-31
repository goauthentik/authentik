import { BaseStage } from "@goauthentik/app/flow/stages/base";



import { property } from "lit/decorators.js";



import { AuthenticatorValidationChallenge, AuthenticatorValidationChallengeResponseRequest, DeviceChallengeResponseRequest, DeviceChallengeTypesRequest } from "@goauthentik/api";


export class BaseDeviceStage<Tin, Tout> extends BaseStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    deviceChallenge?: Tin;

    @property({ type: Boolean })
    showBackButton = false;

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
        const data: AuthenticatorValidationChallengeResponseRequest = {
            selectedChallenge: selectedChallenge,
            selectedChallengeResponse: formData,
            component: this.challenge.component,
        };
        return await this.host.submit(data);
    }
}
