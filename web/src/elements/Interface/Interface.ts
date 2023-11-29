import { config, tenant } from "@goauthentik/common/api/config";
import { UIConfig, uiConfig } from "@goauthentik/common/ui/config";
import {
    authentikConfigContext,
    authentikTenantContext,
} from "@goauthentik/elements/AuthentikContexts";
import type { AdoptedStyleSheetsElement } from "@goauthentik/elements/types";
import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet";

import { ContextProvider } from "@lit-labs/context";
import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Config, CurrentTenant, UiThemeEnum } from "@goauthentik/api";

import { AKElement } from "../Base";

type AkInterface = HTMLElement & {
    getTheme: () => Promise<UiThemeEnum>;
    tenant?: CurrentTenant;
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

    _tenantContext = new ContextProvider(this, {
        context: authentikTenantContext,
        initialValue: undefined,
    });

    _tenant?: CurrentTenant;

    @state()
    set tenant(c: CurrentTenant) {
        this._tenant = c;
        this._tenantContext.setValue(c);
        this.requestUpdate();
    }

    get tenant(): CurrentTenant | undefined {
        return this._tenant;
    }

    constructor() {
        super();
        document.adoptedStyleSheets = [...document.adoptedStyleSheets, ensureCSSStyleSheet(PFBase)];
        tenant().then((tenant) => (this.tenant = tenant));
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
