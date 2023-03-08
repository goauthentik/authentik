import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";

import { LitElement } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";

let css: Promise<string[]> | undefined;
function fetchCustomCSS(): Promise<string[]> {
    if (!css) {
        css = Promise.all(
            Array.of(...document.head.querySelectorAll<HTMLLinkElement>("link[data-inject]")).map(
                (link) => {
                    return fetch(link.href)
                        .then((res) => {
                            return res.text();
                        })
                        .finally(() => {
                            return "";
                        });
                },
            ),
        );
    }
    return css;
}

export class AKElement extends LitElement {
    constructor() {
        super();
        this.addEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
        if (!this.shadowRoot) {
            return;
        }
        this.shadowRoot.adoptedStyleSheets = [...this.shadowRoot.adoptedStyleSheets, AKGlobal];
        fetchCustomCSS().then((sheets) => {
            sheets.map((css) => {
                if (css === "") {
                    return;
                }
                new CSSStyleSheet().replace(css).then((sheet) => {
                    if (!this.shadowRoot) {
                        return;
                    }
                    this.shadowRoot.adoptedStyleSheets = [
                        ...this.shadowRoot.adoptedStyleSheets,
                        sheet,
                    ];
                });
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
