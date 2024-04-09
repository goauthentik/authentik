import { UIConfig, uiConfig } from "@goauthentik/common/ui/config";
import { ModalOrchestrationController } from "@goauthentik/elements/controllers/ModalOrchestrationController.js";
import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet";

import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { Config, CurrentBrand, LicenseSummary } from "@goauthentik/api";
import { UiThemeEnum } from "@goauthentik/api";

import { AKElement } from "../Base";
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

export class Interface extends AKElement implements AkInterface {
    @state()
    uiConfig?: UIConfig;

    [brandContext]!: BrandContextController;

    [configContext]!: ConfigContextController;

    [modalController]!: ModalOrchestrationController;

    @state()
    config?: Config;

    @state()
    brand?: CurrentBrand;

    constructor() {
        super();
        document.adoptedStyleSheets = [...document.adoptedStyleSheets, ensureCSSStyleSheet(PFBase)];
        this[brandContext] = new BrandContextController(this);
        this[configContext] = new ConfigContextController(this);
        this[modalController] = new ModalOrchestrationController(this);
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

export type AkEnterpriseInterface = AkInterface & {
    licenseSummary?: LicenseSummary;
};

const enterpriseContext = Symbol("enterpriseContext");

export class EnterpriseAwareInterface extends Interface {
    [enterpriseContext]!: EnterpriseContextController;

    @state()
    licenseSummary?: LicenseSummary;

    constructor() {
        super();
        this[enterpriseContext] = new EnterpriseContextController(this);
    }
}
