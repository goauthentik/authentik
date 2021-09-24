import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators";

import { CoreApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import { ERROR_CLASS, SECONDARY_CLASS, SUCCESS_CLASS } from "../../constants";
import { PFSize } from "../Spinner";
import { ActionButton } from "./ActionButton";

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
            .catch((err: Error | Response | undefined) => {
                this.buttonClass = ERROR_CLASS;
                if (err instanceof Error) {
                    setTimeout(() => {
                        this.buttonClass = SECONDARY_CLASS;
                    }, 1500);
                    throw err;
                }
                return err?.json().then((errResp) => {
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
                navigator.clipboard.write([
                    new ClipboardItem({
                        "text/plain": (this.callAction() as Promise<string>)
                            .then((key: string) => {
                                this.setDone(SUCCESS_CLASS);
                                return key;
                            })
                            .catch((err: Error) => {
                                this.setDone(ERROR_CLASS);
                                throw err;
                            }),
                    }),
                ]);
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
