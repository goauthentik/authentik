import { BaseStage } from "#flow/stages/base";
import { StageChallengeLike } from "#flow/types";

import { DeviceChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

export class BaseDeviceStage<Tin extends StageChallengeLike, Tout> extends BaseStage<Tin, Tout> {
    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    showBackButton = false;

    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFInputGroup, PFTitle, PFButton];

    submit(payload: Tin): Promise<boolean> {
        return this.host?.submit(payload) || Promise.resolve();
    }

    public reset = () => {
        this.host?.reset?.();
    };

    renderReturnToDevicePicker() {
        if (!this.showBackButton) {
            return nothing;
        }

        return html`<button
            class="pf-c-button pf-m-secondary pf-m-block"
            type="button"
            @click=${this.reset}
        >
            ${msg("Select another authentication method")}
        </button>`;
    }
}
