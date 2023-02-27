import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";

import { LitElement } from "lit";

let css: Promise<string> | undefined;
function fetchCustomCSS(): Promise<string> {
    if (!css) {
        css = fetch("/static/dist/custom.css")
            .then((res) => {
                return res.text();
            })
            .finally(() => {
                return "";
            });
    }
    return css;
}

export class AKElement extends LitElement {
    constructor() {
        super();
        this.addEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
        fetchCustomCSS().then((css) => {
            if (css === "") {
                return;
            }
            new CSSStyleSheet().replace(css).then((sheet) => {
                if (!this.shadowRoot) {
                    return;
                }
                this.shadowRoot.adoptedStyleSheets = [...this.shadowRoot.adoptedStyleSheets, sheet];
            });
        });
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }

    private _handleLocaleChange() {
        this.requestUpdate();
    }
}
