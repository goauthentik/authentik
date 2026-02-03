import { DEFAULT_CONFIG } from "#common/api/config";

import TokenCopyButton from "#elements/buttons/TokenCopyButton/ak-token-copy-button";

import { EndpointsApi, TokenView } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

@customElement("ak-enrollment-token-copy-button")
export class EnrollmentTokenCopyButton extends TokenCopyButton {
    public override entityLabel = msg("Enrollment Token");

    public override callAction(): Promise<TokenView> {
        if (!this.identifier) {
            throw new TypeError("No `identifier` set for `EnrollmentTokenCopyButton`");
        }

        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensViewKeyRetrieve({
            tokenUuid: this.identifier,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enrollment-token-copy-button": EnrollmentTokenCopyButton;
    }
}
