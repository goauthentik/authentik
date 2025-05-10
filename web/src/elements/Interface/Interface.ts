import { setAdoptedStyleSheets } from "@goauthentik/web/common/stylesheets.js";
import {
    $AKBase,
    $PFBase,
    ThemedElement,
    applyUITheme,
    createUIThemeEffect,
} from "@goauthentik/web/common/theme.js";
import { UIConfig } from "@goauthentik/web/common/ui/config.js";
import { AKElement } from "@goauthentik/web/elements/Base.js";
import { VersionContextController } from "@goauthentik/web/elements/Interface/VersionContextController.js";
import { ModalOrchestrationController } from "@goauthentik/web/elements/controllers/ModalOrchestrationController.js";

import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    type Config,
    type CurrentBrand,
    type LicenseSummary,
    UiThemeEnum,
    type Version,
} from "@goauthentik/api";

import { BrandContextController } from "./BrandContextController.js";
import { ConfigContextController } from "./ConfigContextController.js";
import { EnterpriseContextController } from "./EnterpriseContextController.js";

const configContext = Symbol("configContext");
const modalController = Symbol("modalController");
const versionContext = Symbol("versionContext");

export abstract class Interface extends AKElement implements ThemedElement {
    static styles = [PFBase];
    protected [configContext]: ConfigContextController;

    protected [modalController]: ModalOrchestrationController;

    @state()
    public config?: Config;

    @state()
    public brand?: CurrentBrand;

    constructor() {
        super();

        this.dataset.akInterfaceRoot = this.tagName.toLowerCase();

        this.addController(new BrandContextController(this));
        this[configContext] = new ConfigContextController(this);
        this[modalController] = new ModalOrchestrationController(this);

        setAdoptedStyleSheets(document, (currentStyleSheets) => {
            return [...currentStyleSheets, $PFBase, $AKBase];
        });

        if (this.preferredColorScheme === "dark") {
            applyUITheme(document, UiThemeEnum.Dark);
        } else if (this.preferredColorScheme === "auto") {
            createUIThemeEffect((nextUITheme) => applyUITheme(document, nextUITheme));
        }
    }
}

export interface AkAuthenticatedInterface extends ThemedElement {
    licenseSummary?: LicenseSummary;
    version?: Version;
}

const enterpriseContext = Symbol("enterpriseContext");

export class AuthenticatedInterface extends Interface implements AkAuthenticatedInterface {
    [enterpriseContext]!: EnterpriseContextController;
    [versionContext]!: VersionContextController;

    @state()
    public uiConfig?: UIConfig;

    @state()
    public licenseSummary?: LicenseSummary;

    @state()
    public version?: Version;

    constructor() {
        super();

        this[enterpriseContext] = new EnterpriseContextController(this);
        this[versionContext] = new VersionContextController(this);
    }
}
