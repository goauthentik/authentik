import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
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
    _mediaMatcher?: MediaQueryList;
    _mediaMatcherHandler?: (ev?: MediaQueryListEvent) => void;
    _activeTheme?: UiThemeEnum;

    get activeTheme(): UiThemeEnum | undefined {
        return this._activeTheme;
    }

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

    async _initTheme(root: AdoptedStyleSheetsElement): Promise<void> {
        rootInterface()?._initTheme(root);
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

    _applyTheme(root: AdoptedStyleSheetsElement, theme?: UiThemeEnum): void {
        if (!theme) {
            theme = UiThemeEnum.Automatic;
        }
        if (theme === UiThemeEnum.Automatic) {
            // Create a media matcher to automatically switch the theme depending on
            // prefers-color-scheme
            if (!this._mediaMatcher) {
                this._mediaMatcher = window.matchMedia("(prefers-color-scheme: light)");
                this._mediaMatcherHandler = (ev?: MediaQueryListEvent) => {
                    const theme =
                        ev?.matches || this._mediaMatcher?.matches
                            ? UiThemeEnum.Light
                            : UiThemeEnum.Dark;
                    this._activateTheme(root, theme);
                };
                this._mediaMatcher.addEventListener("change", this._mediaMatcherHandler);
                this._mediaMatcherHandler();
            }
            return;
        } else if (this._mediaMatcher && this._mediaMatcherHandler) {
            // Theme isn't automatic and we have a matcher configured, remove the matcher
            // to prevent changes
            this._mediaMatcher.removeEventListener("change", this._mediaMatcherHandler);
            this._mediaMatcher = undefined;
        }
        this._activateTheme(root, theme);
    }

    _activateTheme(root: AdoptedStyleSheetsElement, theme: UiThemeEnum) {
        // Make sure we only get to this callback once we've picked a concise theme choice
        this.themeChangeCallback(theme);
        this._activeTheme = theme;
        this.setAttribute("theme", theme);
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
    _activateTheme(root: AdoptedStyleSheetsElement, theme: UiThemeEnum): void {
        super._activateTheme(root, theme);
        super._activateTheme(document, theme);
    }

    async _initTheme(root: AdoptedStyleSheetsElement): Promise<void> {
        const bootstrapTheme = globalAK()?.tenant.uiTheme || UiThemeEnum.Automatic;
        this._applyTheme(root, bootstrapTheme);
        uiConfig().then((config) => {
            if (config.theme.base) {
                this._applyTheme(root, config.theme.base);
            }
        });
    }
}
