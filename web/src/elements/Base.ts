import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";

import { localized } from "@lit/localize";
import { LitElement } from "lit";

@localized()
export class AKElement extends LitElement {
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
