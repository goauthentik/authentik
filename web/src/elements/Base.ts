import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";
import { uiConfig } from "@goauthentik/common/ui/config";

import { LitElement } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import ThemeDark from "@goauthentik/common/styles/theme-dark.css";

import { UiThemeEnum } from "@goauthentik/api";

export function rootInterface(): Interface | undefined {
    const el = Array.from(document.body.querySelectorAll("*")).filter(
        (el) => el instanceof Interface,
    );
    return el[0] as Interface;
}

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

export interface AdoptedStyleSheetsElement {
    adoptedStyleSheets: readonly CSSStyleSheet[];
}

export class AKElement extends LitElement {
    constructor() {
        super();
        this.addEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }

    protected createRenderRoot(): ShadowRoot | Element {
        const root = super.createRenderRoot() as ShadowRoot;
        root.adoptedStyleSheets = [...root.adoptedStyleSheets, AKGlobal];
        this._initTheme(root);
        this._initCustomCSS(root);
        return root;
    }

    private async _initTheme(root: AdoptedStyleSheetsElement): Promise<void> {
        const theme = await rootInterface()?._getThemeFromConfig();
        if (!theme || theme === UiThemeEnum.Automatic) {
            const matcher = window.matchMedia("(prefers-color-scheme: light)");
            const handler = (ev?: MediaQueryListEvent) => {
                const theme = ev?.matches || matcher.matches ? UiThemeEnum.Light : UiThemeEnum.Dark;
                this._updateTheme(root, theme);
            };
            matcher.addEventListener("change", handler);
            handler();
        } else {
            this._updateTheme(root, theme);
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
    themeChangeCallback(theme: UiThemeEnum): void {
        return;
    }

    _updateTheme(root: AdoptedStyleSheetsElement, theme: UiThemeEnum): void {
        this.themeChangeCallback(theme);
        let stylesheet: CSSStyleSheet | undefined;
        if (theme === UiThemeEnum.Dark) {
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

export class Interface extends AKElement {
    _updateTheme(root: AdoptedStyleSheetsElement, theme: UiThemeEnum): void {
        super._updateTheme(root, theme);
        super._updateTheme(document, theme);
    }

    async _getThemeFromConfig(): Promise<UiThemeEnum> {
        return (await uiConfig()).theme.base;
    }
}
