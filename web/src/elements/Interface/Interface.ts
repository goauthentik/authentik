import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { brand, config } from "@goauthentik/common/api/config";
import { UIConfig, uiConfig } from "@goauthentik/common/ui/config";
import {
    authentikBrandContext,
    authentikConfigContext,
    authentikVersionContext,
} from "@goauthentik/elements/AuthentikContexts";
import type { AdoptedStyleSheetsElement } from "@goauthentik/elements/types";
import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet";

import { ContextProvider } from "@lit-labs/context";
import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AdminApi,
    Config,
    CurrentTenant as CurrentBrand,
    UiThemeEnum,
    Version,
} from "@goauthentik/api";

import { AKElement } from "../Base";

type AkInterface = HTMLElement & {
    getTheme: () => Promise<UiThemeEnum>;
    brand?: CurrentBrand;
    uiConfig?: UIConfig;
    config?: Config;
};

export class Interface extends AKElement implements AkInterface {
    @state()
    uiConfig?: UIConfig;

    _configContext = new ContextProvider(this, {
        context: authentikConfigContext,
        initialValue: undefined,
    });

    _config?: Config;

    @state()
    set config(c: Config) {
        this._config = c;
        this._configContext.setValue(c);
        this.requestUpdate();
    }

    get config(): Config | undefined {
        return this._config;
    }

    _brandContext = new ContextProvider(this, {
        context: authentikBrandContext,
        initialValue: undefined,
    });

    _brand?: CurrentBrand;

    @state()
    set brand(c: CurrentBrand) {
        this._brand = c;
        this._brandContext.setValue(c);
        this.requestUpdate();
    }

    get brand(): CurrentBrand | undefined {
        return this._brand;
    }

    _versionContext = new ContextProvider(this, {
        context: authentikVersionContext,
        initialValue: undefined,
    });

    _version?: Version;

    @state()
    set version(v: Version) {
        this._version = v;
        this._versionContext.setValue(v);
        console.log(`Version set to ${v}`);
        this.requestUpdate();
    }

    get version(): Version | undefined {
        return this._version;
    }

    constructor() {
        super();
        document.adoptedStyleSheets = [...document.adoptedStyleSheets, ensureCSSStyleSheet(PFBase)];
        brand().then((brand) => (this.brand = brand));
        config().then((config) => (this.config = config));
        new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve().then((version) => {
            this.version = version;
        });
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
