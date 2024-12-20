import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { MessageLevel } from "@goauthentik/common/messages";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import { writeToClipboard } from "@goauthentik/elements/utils/writeToClipboard";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, ResponseError, TokenView } from "@goauthentik/api";

import { APIMessage } from "../../messages/Message";
import BaseTaskButton from "../SpinnerButton/BaseTaskButton";

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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isTokenView = (v: any): v is TokenView => v && "key" in v && typeof v.key === "string";

@customElement("ak-token-copy-button")
export class TokenCopyButton extends BaseTaskButton {
    /**
     * The identifier key associated with this token.
     * @attr
     */
    @property()
    identifier?: string;

    constructor() {
        super();
        this.onSuccess = this.onSuccess.bind(this);
        this.onError = this.onError.bind(this);
    }

    callAction: () => Promise<unknown> = () => {
        if (!this.identifier) {
            return Promise.reject();
        }
        return new CoreApi(DEFAULT_CONFIG).coreTokensViewKeyRetrieve({
            identifier: this.identifier,
        });
    };

    async onSuccess(token: unknown) {
        super.onSuccess(token);
        if (!isTokenView(token)) {
            throw new Error(`Unrecognized return from server: ${token}`);
        }
        const wroteToClipboard = await writeToClipboard(token.key as string);
        const info: Pick<APIMessage, "message" | "description"> = wroteToClipboard
            ? {
                  message: msg("The token has been copied to your clipboard"),
              }
            : {
                  message: token.key,
                  description: msg(
                      "The token was displayed because authentik does not have permission to write to the clipboard",
                  ),
              };
        showMessage({
            level: MessageLevel.info,
            ...info,
        });
    }

    async onError(error: unknown) {
        super.onError(error);
        // prettier-ignore
        const message = error instanceof ResponseError ? await error.response.text()
            : error instanceof Error ? error.toString()
            : `${error}`;

        showMessage({
            level: MessageLevel.error,
            message,
        });
    }
}

export default TokenCopyButton;

declare global {
    interface HTMLElementTagNameMap {
        "ak-token-copy-button": TokenCopyButton;
    }
}
