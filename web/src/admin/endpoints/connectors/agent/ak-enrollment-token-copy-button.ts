import { DEFAULT_CONFIG } from "#common/api/config";

import TokenCopyButton from "#elements/buttons/TokenCopyButton/ak-token-copy-button";

import { EndpointsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-enrollment-token-copy-button")
export class EnrollmentTokenCopyButton extends TokenCopyButton {
    callAction: () => Promise<unknown> = () => {
        if (!this.identifier) {
            return Promise.reject();
        }
        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensViewKeyRetrieve({
            tokenUuid: this.identifier,
        });
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enrollment-token-copy-button": EnrollmentTokenCopyButton;
    }
}
