import { UIConfig, uiConfig } from "@goauthentik/common/ui/config";
import { VersionContextController } from "@goauthentik/elements/Interface/VersionContextController";
import { ModalOrchestrationController } from "@goauthentik/elements/controllers/ModalOrchestrationController.js";
import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet";

import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { Config, CurrentBrand, LicenseSummary, Version } from "@goauthentik/api";
import { UiThemeEnum } from "@goauthentik/api";

import { AKElement, rootInterface } from "../Base";
import { BrandContextController } from "./BrandContextController";
import { ConfigContextController } from "./ConfigContextController";
import { EnterpriseContextController } from "./EnterpriseContextController";

export type AkInterface = HTMLElement & {
    getTheme: () => Promise<UiThemeEnum>;
    brand?: CurrentBrand;
    uiConfig?: UIConfig;
    config?: Config;
};

const brandContext = Symbol("brandContext");
const configContext = Symbol("configContext");
const modalController = Symbol("modalController");
const versionContext = Symbol("versionContext");

export class Interface extends AKElement implements AkInterface {
    [brandContext]!: BrandContextController;

    [configContext]!: ConfigContextController;

    [modalController]!: ModalOrchestrationController;

    @state()
    uiConfig?: UIConfig;

    @state()
    config?: Config;

    @state()
    brand?: CurrentBrand;

    constructor() {
        super();
        document.adoptedStyleSheets = [...document.adoptedStyleSheets, ensureCSSStyleSheet(PFBase)];
        this._initContexts();
        this.dataset.akInterfaceRoot = "true";
    }

    _initContexts() {
        this[brandContext] = new BrandContextController(this);
        this[configContext] = new ConfigContextController(this);
        this[modalController] = new ModalOrchestrationController(this);
    }

    _activateTheme(theme: UiThemeEnum, ...roots: DocumentOrShadowRoot[]): void {
        if (theme === this._activeTheme) {
            return;
        }
        console.debug(
            `authentik/interface[${rootInterface()?.tagName.toLowerCase()}]: Enabling theme ${theme}`,
        );
        // Special case for root interfaces, as they need to modify the global document CSS too
        // Instead of calling ._activateTheme() twice, we insert the root document in the call
        // since multiple calls to ._activateTheme() would not do anything after the first call
        // as the theme is already enabled.
        roots.unshift(document as unknown as DocumentOrShadowRoot);
        super._activateTheme(theme, ...roots);
    }

    async getTheme(): Promise<UiThemeEnum> {
        if (!this.uiConfig) {
            this.uiConfig = await uiConfig();
        }
        return this.uiConfig.theme?.base || UiThemeEnum.Automatic;
    }
}

export type AkAuthenticatedInterface = AkInterface & {
    licenseSummary?: LicenseSummary;
    version?: Version;
};

const enterpriseContext = Symbol("enterpriseContext");

export class AuthenticatedInterface extends Interface {
    [enterpriseContext]!: EnterpriseContextController;
    [versionContext]!: VersionContextController;

    @state()
    licenseSummary?: LicenseSummary;

    @state()
    version?: Version;

    _initContexts(): void {
        super._initContexts();
        this[enterpriseContext] = new EnterpriseContextController(this);
        this[versionContext] = new VersionContextController(this);
    }
}
