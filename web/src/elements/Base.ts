import { brand, config } from "@goauthentik/common/api/config";
import { EVENT_THEME_CHANGE } from "@goauthentik/common/constants";
import { UIConfig, uiConfig } from "@goauthentik/common/ui/config";
import { adaptCSS } from "@goauthentik/common/utils";

import { localized } from "@lit/localize";
import { CSSResult, LitElement } from "lit";
import { state } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import ThemeDark from "@goauthentik/common/styles/theme-dark.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Config, CurrentBrand, UiThemeEnum } from "@goauthentik/api";

type AkInterface = HTMLElement & {
    getTheme: () => Promise<UiThemeEnum>;
    brand?: CurrentBrand;
    uiConfig?: UIConfig;
    config?: Config;
};

export const rootInterface = <T extends AkInterface>(): T | undefined =>
    (document.body.querySelector("[data-ak-interface-root]") as T) ?? undefined;

export function ensureCSSStyleSheet(css: CSSStyleSheet | CSSResult): CSSStyleSheet {
    if (css instanceof CSSResult) {
        return css.styleSheet!;
    }
    return css;
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

@localized()
export class AKElement extends LitElement {
    _mediaMatcher?: MediaQueryList;
    _mediaMatcherHandler?: (ev?: MediaQueryListEvent) => void;
    _activeTheme?: UiThemeEnum;

    get activeTheme(): UiThemeEnum | undefined {
        return this._activeTheme;
    }

    constructor() {
        super();
    }

    protected createRenderRoot(): ShadowRoot | Element {
        const root = super.createRenderRoot() as ShadowRoot;
        let styleRoot: AdoptedStyleSheetsElement = root;
        if ("ShadyDOM" in window) {
            styleRoot = document;
        }
        styleRoot.adoptedStyleSheets = adaptCSS([
            ...styleRoot.adoptedStyleSheets,
            ensureCSSStyleSheet(AKGlobal),
        ]);
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
            root.adoptedStyleSheets = [...root.adoptedStyleSheets, ensureCSSStyleSheet(stylesheet)];
        }
        if (oldStylesheet) {
            root.adoptedStyleSheets = root.adoptedStyleSheets.filter((v) => v !== oldStylesheet);
        }
        this._activeTheme = theme;
        this.requestUpdate();
    }
}

export class Interface extends AKElement implements AkInterface {
    @state()
    brand?: CurrentBrand;

    @state()
    uiConfig?: UIConfig;

    @state()
    config?: Config;

    constructor() {
        super();
        document.adoptedStyleSheets = [...document.adoptedStyleSheets, ensureCSSStyleSheet(PFBase)];
        brand().then((brand) => (this.brand = brand));
        config().then((config) => (this.config = config));
        this.dataset.akInterfaceRoot = "true";
    }

    _activateTheme(root: AdoptedStyleSheetsElement, theme: UiThemeEnum): void {
        super._activateTheme(root, theme);
        super._activateTheme(document, theme);
    }

    async getTheme(): Promise<UiThemeEnum> {
        if (!this.uiConfig) {
            this.uiConfig = await uiConfig();
        }
        return this.uiConfig.theme?.base || UiThemeEnum.Automatic;
    }
}
