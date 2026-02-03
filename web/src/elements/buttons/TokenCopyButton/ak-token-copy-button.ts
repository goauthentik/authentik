import { DEFAULT_CONFIG } from "#common/api/config";
import { writeToClipboard } from "#common/clipboard";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { BaseTaskButton } from "#elements/buttons/SpinnerButton/BaseTaskButton";
import { showMessage } from "#elements/messages/MessageContainer";

import { CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

/**
 * A derivative of ak-action-button that is used only to request tokens from the back-end server.
 * Automatically pushes tokens to the clipboard, if the clipboard is available; otherwise displays
 * them in the notifications.
 *
 * @element ak-token-copy-button
 *
 * @slot - The label for the button
 *
 * @fires ak-button-click - When the button is first clicked.
 * @fires ak-button-success - When the async process succeeds
 * @fires ak-button-failure - When the async process fails
 * @fires ak-button-reset - When the button is reset after the async process completes
 */

@customElement("ak-token-copy-button")
export class TokenCopyButton extends BaseTaskButton<null> {
    /**
     * The identifier key associated with this token.
     * @attr
     */
    @property({ type: String })
    public identifier: string | null = null;

    @property({ type: String, attribute: "entity-label" })
    public entityLabel: string = msg("Token");

    public override callAction() {
        if (!this.identifier) {
            throw new TypeError("No `identifier` set for `TokenCopyButton`");
        }

        // Safari permission hack.
        const text = new ClipboardItem({
            "text/plain": new CoreApi(DEFAULT_CONFIG)
                .coreTokensViewKeyRetrieve({
                    identifier: this.identifier,
                })
                .then((tokenView) => new Blob([tokenView.key], { type: "text/plain" })),
        });

        return writeToClipboard(text, this.entityLabel).then(() => null);
    }

    protected async onError(error: unknown) {
        super.onError(error);
        const parsedError = await parseAPIResponseError(error);

        showMessage({
            level: MessageLevel.error,
            message: pluckErrorDetail(
                parsedError,
                msg("An unknown error occurred while retrieving the token."),
            ),
        });
    }
}

export default TokenCopyButton;

declare global {
    interface HTMLElementTagNameMap {
        "ak-token-copy-button": TokenCopyButton;
    }
}
