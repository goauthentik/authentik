import { EVENT_LOCALE_CHANGE, EVENT_THEME_CHANGE } from "@goauthentik/common/constants";
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

const QUERY_MEDIA_COLOR_LIGHT = "(prefers-color-scheme: light)";

export class AKElement extends LitElement {
    _mediaMatcher?: MediaQueryList;
    _mediaMatcherHandler?: (ev?: MediaQueryListEvent) => void;
    _activeTheme?: UiThemeEnum;

    get activeTheme(): UiThemeEnum | undefined {
        return this._activeTheme;
    }
    private _handleLocaleChange: () => void;

    constructor() {
        super();
        this._handleLocaleChange = (() => {
            this.requestUpdate();
        }).bind(this);
        window.addEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }

    protected createRenderRoot(): ShadowRoot | Element {
        const root = super.createRenderRoot() as ShadowRoot;
        let styleRoot: AdoptedStyleSheetsElement = root;
        if ("ShadyDOM" in window) {
            styleRoot = document;
        }
        styleRoot.adoptedStyleSheets = [...styleRoot.adoptedStyleSheets, AKGlobal];
        this._initTheme(styleRoot);
        this._initCustomCSS(styleRoot);
        return root;
    }

    async getTheme(): Promise<UiThemeEnum> {
        return rootInterface()?.getTheme() || UiThemeEnum.Automatic;
    }

    async _initTheme(root: AdoptedStyleSheetsElement): Promise<void> {
        // Early activate theme based on media query to prevent light flash
        // when dark is preferred
        this._activateTheme(
            root,
            window.matchMedia(QUERY_MEDIA_COLOR_LIGHT).matches
                ? UiThemeEnum.Light
                : UiThemeEnum.Dark,
        );
        this._applyTheme(root, await this.getTheme());
    }

    private async _initCustomCSS(root: AdoptedStyleSheetsElement): Promise<void> {
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

    _applyTheme(root: AdoptedStyleSheetsElement, theme?: UiThemeEnum): void {
        if (!theme) {
            theme = UiThemeEnum.Automatic;
        }
        if (theme === UiThemeEnum.Automatic) {
            // Create a media matcher to automatically switch the theme depending on
            // prefers-color-scheme
            if (!this._mediaMatcher) {
                this._mediaMatcher = window.matchMedia(QUERY_MEDIA_COLOR_LIGHT);
                this._mediaMatcherHandler = (ev?: MediaQueryListEvent) => {
                    const theme =
                        ev?.matches || this._mediaMatcher?.matches
                            ? UiThemeEnum.Light
                            : UiThemeEnum.Dark;
                    this._activateTheme(root, theme);
                };
                this._mediaMatcher.addEventListener("change", this._mediaMatcherHandler);
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

    static themeToStylesheet(theme?: UiThemeEnum): CSSStyleSheet | undefined {
        if (theme === UiThemeEnum.Dark) {
            return ThemeDark;
        }
        return undefined;
    }

    _activateTheme(root: AdoptedStyleSheetsElement, theme: UiThemeEnum) {
        if (theme === this._activeTheme) {
            return;
        }
        // Make sure we only get to this callback once we've picked a concise theme choice
        this.dispatchEvent(
            new CustomEvent(EVENT_THEME_CHANGE, {
                bubbles: true,
                composed: true,
                detail: theme,
            }),
        );
        this.setAttribute("theme", theme);
        const stylesheet = AKElement.themeToStylesheet(theme);
        const oldStylesheet = AKElement.themeToStylesheet(this._activeTheme);
        if (stylesheet) {
            root.adoptedStyleSheets = [...root.adoptedStyleSheets, stylesheet];
        }
        if (oldStylesheet) {
            root.adoptedStyleSheets = root.adoptedStyleSheets.filter((v) => v !== oldStylesheet);
        }
        this._activeTheme = theme;
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_LOCALE_CHANGE, this._handleLocaleChange);
    }
}

export class Interface extends AKElement {
    _activateTheme(root: AdoptedStyleSheetsElement, theme: UiThemeEnum): void {
        super._activateTheme(root, theme);
        super._activateTheme(document, theme);
    }

    async getTheme(): Promise<UiThemeEnum> {
        const config = await uiConfig();
        return config.theme?.base || UiThemeEnum.Automatic;
    }
}
