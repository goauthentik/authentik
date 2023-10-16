import { LOCALSTORAGE_AUTHENTIK_KEY } from "@goauthentik/common/constants";

import { msg } from "@lit/localize";
import { LitElement, ReactiveController, ReactiveControllerHost, html } from "lit";

type ReactiveLitElement = LitElement & ReactiveControllerHost;

export interface ShowHintControllerHost extends ReactiveLitElement {
    showHint: boolean;

    showHintController: ShowHintController;
}

const getCurrentStorageValue = (): Record<string, unknown> => {
    try {
        return JSON.parse(window?.localStorage.getItem(LOCALSTORAGE_AUTHENTIK_KEY) ?? "{}");
    } catch (_err: unknown) {
        return {};
    }
};

export class ShowHintController implements ReactiveController {
    host: ShowHintControllerHost;

    hintToken: string;

    constructor(host: ShowHintControllerHost, hintToken: string) {
        (this.host = host).addController(this);
        this.hintToken = hintToken;
        this.hideTheHint = this.hideTheHint.bind(this);
    }

    hideTheHint() {
        window?.localStorage.setItem(
            LOCALSTORAGE_AUTHENTIK_KEY,
            JSON.stringify({
                ...getCurrentStorageValue(),
                [this.hintToken]: false,
            }),
        );
        this.host.showHint = false;
    }

    hostConnected() {
        const localStores = getCurrentStorageValue();
        if (!(this.hintToken in localStores)) {
            return;
        }
        // Note that we only do this IF the field exists and is defined. `undefined` means "do the
        // default thing of showing the hint."
        this.host.showHint = localStores[this.hintToken] as boolean;
    }

    render() {
        return html`<ak-hint-footer
            ><div style="text-align: right">
                <input type="checkbox" @input=${this.hideTheHint} />${msg(
                    "Don't show this message again.",
                )}
            </div></ak-hint-footer
        >`;
    }
}
