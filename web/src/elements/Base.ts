import { EVENT_LOCALE_CHANGE } from "@goauthentik/web/common/constants";

import { LitElement } from "lit";

import AKGlobal from "./styles/authentik.css";

export class AKElement extends LitElement {
    static GlobalStyle = AKGlobal;

    constructor() {
        super();
        this.addEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }

    private _handleLocaleChange() {
        this.requestUpdate();
    }
}
