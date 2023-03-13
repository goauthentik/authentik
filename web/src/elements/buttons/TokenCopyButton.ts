import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ERROR_CLASS, SECONDARY_CLASS, SUCCESS_CLASS } from "@goauthentik/common/constants";
import { MessageLevel } from "@goauthentik/common/messages";
import { PFSize } from "@goauthentik/elements/Spinner";
import { ActionButton } from "@goauthentik/elements/buttons/ActionButton";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, ResponseError } from "@goauthentik/api";

@customElement("ak-token-copy-button")
export class TokenCopyButton extends ActionButton {
    @property()
    identifier?: string;

    @property()
    buttonClass: string = SECONDARY_CLASS;

    apiRequest: () => Promise<unknown> = () => {
        this.setLoading();
        if (!this.identifier) {
            return Promise.reject();
        }
        return new CoreApi(DEFAULT_CONFIG)
            .coreTokensViewKeyRetrieve({
                identifier: this.identifier,
            })
            .then((token) => {
                if (!token.key) {
                    return Promise.reject();
                }
                setTimeout(() => {
                    this.buttonClass = SECONDARY_CLASS;
                }, 1500);
                this.buttonClass = SUCCESS_CLASS;
                return token.key;
            })
            .catch((err: Error | ResponseError | undefined) => {
                this.buttonClass = ERROR_CLASS;
                if (!(err instanceof ResponseError)) {
                    setTimeout(() => {
                        this.buttonClass = SECONDARY_CLASS;
                    }, 1500);
                    throw err;
                }
                return err.response.json().then((errResp) => {
                    setTimeout(() => {
                        this.buttonClass = SECONDARY_CLASS;
                    }, 1500);
                    throw new Error(errResp["detail"]);
                });
            });
    };

    render(): TemplateResult {
        return html`<button
            class="pf-c-button pf-m-progress ${this.classList.toString()}"
            @click=${() => {
                if (this.isRunning === true) {
                    return;
                }
                this.setLoading();
                // If we're on an insecure origin (non-https and not localhost), we might
                // not be able to write to the clipboard, and instead show a message
                if (!navigator.clipboard) {
                    this.callAction()
                        .then((v) => {
                            this.setDone(SUCCESS_CLASS);
                            showMessage({
                                level: MessageLevel.info,
                                message: v as string,
                            });
                        })
                        .catch((err: Error) => {
                            this.setDone(ERROR_CLASS);
                            throw err;
                        });
                    return;
                }
                // Because safari is stupid, it only allows navigator.clipboard.write directly
                // in the @click handler.
                // And also chrome is stupid, because it doesn't accept Promises as values for
                // ClipboardItem, so now there's two implementations
                if (
                    navigator.userAgent.includes("Safari") &&
                    !navigator.userAgent.includes("Chrome")
                ) {
                    navigator.clipboard.write([
                        new ClipboardItem({
                            "text/plain": (this.callAction() as Promise<string>)
                                .then((key: string) => {
                                    this.setDone(SUCCESS_CLASS);
                                    return new Blob([key], {
                                        type: "text/plain",
                                    });
                                })
                                .catch((err: Error) => {
                                    this.setDone(ERROR_CLASS);
                                    throw err;
                                }),
                        }),
                    ]);
                } else {
                    (this.callAction() as Promise<string>)
                        .then((key: string) => {
                            navigator.clipboard.writeText(key).then(() => {
                                this.setDone(SUCCESS_CLASS);
                            });
                        })
                        .catch((err: ResponseError | Error) => {
                            if (!(err instanceof ResponseError)) {
                                showMessage({
                                    level: MessageLevel.error,
                                    message: err.message,
                                });
                                return;
                            }
                            return err.response.json().then((errResp) => {
                                this.setDone(ERROR_CLASS);
                                throw new Error(errResp["detail"]);
                            });
                        });
                }
            }}
        >
            ${this.isRunning
                ? html`<span class="pf-c-button__progress">
                      <ak-spinner size=${PFSize.Medium}></ak-spinner>
                  </span>`
                : ""}
            <slot></slot>
        </button>`;
    }
}
