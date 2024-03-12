import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { brand, config } from "@goauthentik/common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "@goauthentik/common/constants";
import { UIConfig, uiConfig } from "@goauthentik/common/ui/config";
import {
    authentikBrandContext,
    authentikConfigContext,
    authentikEnterpriseContext,
} from "@goauthentik/elements/AuthentikContexts";
import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet";

import { ContextProvider } from "@lit/context";
import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { Config, CurrentBrand, LicenseSummary } from "@goauthentik/api";
import { EnterpriseApi, UiThemeEnum } from "@goauthentik/api";

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

    constructor() {
        super();
        document.adoptedStyleSheets = [...document.adoptedStyleSheets, ensureCSSStyleSheet(PFBase)];
        brand().then((brand) => (this.brand = brand));
        config().then((config) => (this.config = config));

        this.dataset.akInterfaceRoot = "true";
    }

    _activateTheme(root: DocumentOrShadowRoot, theme: UiThemeEnum): void {
        super._activateTheme(root, theme);
        super._activateTheme(document as unknown as DocumentOrShadowRoot, theme);
    }

    async getTheme(): Promise<UiThemeEnum> {
        if (!this.uiConfig) {
            this.uiConfig = await uiConfig();
        }
        return this.uiConfig.theme?.base || UiThemeEnum.Automatic;
    }
}

export class EnterpriseAwareInterface extends Interface {
    _licenseSummaryContext = new ContextProvider(this, {
        context: authentikEnterpriseContext,
        initialValue: undefined,
    });

    _licenseSummary?: LicenseSummary;

    @state()
    set licenseSummary(c: LicenseSummary) {
        this._licenseSummary = c;
        this._licenseSummaryContext.setValue(c);
        this.requestUpdate();
    }

    get licenseSummary(): LicenseSummary | undefined {
        return this._licenseSummary;
    }

    constructor() {
        super();
        const refreshStatus = () => {
            new EnterpriseApi(DEFAULT_CONFIG)
                .enterpriseLicenseSummaryRetrieve()
                .then((enterprise) => {
                    this.licenseSummary = enterprise;
                });
        };
        refreshStatus();
        window.addEventListener(EVENT_REFRESH_ENTERPRISE, () => {
            refreshStatus();
        });
    }
}
