import { LOCALSTORAGE_AUTHENTIK_KEY } from "#common/constants";

import { msg } from "@lit/localize";
import { html, LitElement, ReactiveController, ReactiveControllerHost } from "lit";

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
    #host: ShowHintControllerHost;

    protected hintToken: string;

    public constructor(host: ShowHintControllerHost, hintToken: string) {
        this.#host = host;
        this.#host.addController(this);
        this.hintToken = hintToken;
    }

    protected setTheHint(state: boolean = false) {
        window?.localStorage.setItem(
            LOCALSTORAGE_AUTHENTIK_KEY,
            JSON.stringify({
                ...getCurrentStorageValue(),
                [this.hintToken]: state,
            }),
        );
        this.#host.showHint = state;
    }

    public hide = () => {
        this.setTheHint(false);
    };

    public show = () => {
        this.setTheHint(true);
    };

    public hostConnected() {
        const localStores = getCurrentStorageValue();
        if (!(this.hintToken in localStores)) {
            return;
        }
        // Note that we only do this IF the field exists and is defined. `undefined` means "do the
        // default thing of showing the hint."
        this.#host.showHint = localStores[this.hintToken] as boolean;
    }

    public render() {
        return html`<ak-hint-footer
            ><div style="text-align: right">
                <input type="checkbox" @input=${this.hide} />&nbsp;${msg(
                    "Don't show this message again.",
                )}
            </div></ak-hint-footer
        >`;
    }
}
