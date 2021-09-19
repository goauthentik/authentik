import { customElement, property } from "lit-element";
import { CoreApi } from "@goauthentik/api";
import { SECONDARY_CLASS, SUCCESS_CLASS } from "../../constants";
import { DEFAULT_CONFIG } from "../../api/Config";
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
                return navigator.clipboard.writeText(token.key).then(() => {
                    this.buttonClass = SUCCESS_CLASS;
                    setTimeout(() => {
                        this.buttonClass = SECONDARY_CLASS;
                    }, 1500);
                });
            })
            .catch((err: Response | undefined) => {
                return err?.json().then((errResp) => {
                    throw new Error(errResp["detail"]);
                });
            });
    };
}
