import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";
import { Themes, uiConfig } from "@goauthentik/common/ui/config";

import { LitElement } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import ThemeDark from "@goauthentik/common/styles/theme-dark.css";

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

interface AdoptedStyleSheetsElement {
    adoptedStyleSheets: readonly CSSStyleSheet[];
}

export class AKElement extends LitElement {
    constructor(private _isInterface: boolean = false) {
        super();
        this.addEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }

    protected createRenderRoot(): ShadowRoot {
        const root = super.createRenderRoot() as ShadowRoot;
        root.adoptedStyleSheets = [...root.adoptedStyleSheets, AKGlobal];
        this._initTheme(root);
        this._initCustomCSS(root);
        return root;
    }

    private async _initTheme(root: AdoptedStyleSheetsElement): Promise<void> {
        const config = await uiConfig();
        if (config.theme.base === Themes.automatic) {
            const matcher = window.matchMedia("(prefers-color-scheme: light)");
            const handler = (ev?: MediaQueryListEvent) => {
                const theme = ev?.matches || matcher.matches ? Themes.light : Themes.dark;
                this._updateTheme(root, theme);
                if (this._isInterface) {
                    this._updateTheme(document, theme);
                }
            };
            matcher.addEventListener("change", handler);
            handler();
        } else {
            this._updateTheme(root, config.theme.base);
            if (this._isInterface) {
                this._updateTheme(document, config.theme.base);
            }
        }
    }

    private async _initCustomCSS(root: ShadowRoot): Promise<void> {
        const sheets = await fetchCustomCSS();
        sheets.map((css) => {
            if (css === "") {
                return;
            }
            new CSSStyleSheet().replace(css).then((sheet) => {
                root.adoptedStyleSheets = [...root.adoptedStyleSheets, sheet];
            });
        });
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    themeChangeCallback(theme: Themes): void {
        return;
    }

    private _updateTheme(root: AdoptedStyleSheetsElement, theme: Themes): void {
        this.themeChangeCallback(theme);
        let stylesheet: CSSStyleSheet | undefined;
        if (theme === Themes.dark) {
            stylesheet = ThemeDark;
        }
        if (!stylesheet) {
            return;
        }
        if (root.adoptedStyleSheets.indexOf(stylesheet) === -1) {
            root.adoptedStyleSheets = [...root.adoptedStyleSheets, stylesheet];
        } else {
            root.adoptedStyleSheets = root.adoptedStyleSheets.filter((v) => v !== stylesheet);
        }
        this.requestUpdate();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }

    private _handleLocaleChange() {
        this.requestUpdate();
    }
}
