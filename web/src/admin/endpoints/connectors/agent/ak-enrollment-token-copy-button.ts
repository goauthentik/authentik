import { DEFAULT_CONFIG } from "#common/api/config";
import { writeToClipboard } from "#common/clipboard";

import TokenCopyButton from "#elements/buttons/TokenCopyButton/ak-token-copy-button";

import { EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

@customElement("ak-enrollment-token-copy-button")
export class EnrollmentTokenCopyButton extends TokenCopyButton {
    public override entityLabel = msg("Enrollment Token");

    public override callAction(): Promise<null> {
        if (!this.identifier) {
            throw new TypeError("No `identifier` set for `EnrollmentTokenCopyButton`");
        }

        // Safari permission hack.
        const text = new ClipboardItem({
            "text/plain": new EndpointsApi(DEFAULT_CONFIG)
                .endpointsAgentsEnrollmentTokensViewKeyRetrieve({
                    tokenUuid: this.identifier,
                })
                .then((tokenView) => new Blob([tokenView.key], { type: "text/plain" })),
        });

        return writeToClipboard(text, this.entityLabel).then(() => null);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enrollment-token-copy-button": EnrollmentTokenCopyButton;
    }
}
