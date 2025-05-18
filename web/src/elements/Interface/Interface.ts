import { globalAK } from "@goauthentik/common/global.js";
import { ThemedElement, applyDocumentTheme } from "@goauthentik/common/theme.js";
import { UIConfig } from "@goauthentik/common/ui/config.js";
import { AKElement } from "@goauthentik/elements/Base.js";
import { VersionContextController } from "@goauthentik/elements/Interface/VersionContextController.js";
import { ModalOrchestrationController } from "@goauthentik/elements/controllers/ModalOrchestrationController.js";

import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    type Config,
    type CurrentBrand,
    type LicenseSummary,
    type Version,
} from "@goauthentik/api";

import { BrandContextController } from "./BrandContextController.js";
import { ConfigContextController } from "./ConfigContextController.js";
import { EnterpriseContextController } from "./EnterpriseContextController.js";

const configContext = Symbol("configContext");
const modalController = Symbol("modalController");
const versionContext = Symbol("versionContext");

export abstract class LightInterface extends AKElement implements ThemedElement {
    constructor() {
        super();
        this.dataset.akInterfaceRoot = this.tagName.toLowerCase();

        if (!document.documentElement.dataset.theme) {
            applyDocumentTheme(globalAK().brand.uiTheme);
        }
    }
}

export abstract class Interface extends LightInterface implements ThemedElement {
    static styles = [PFBase];
    protected [configContext]: ConfigContextController;

    protected [modalController]: ModalOrchestrationController;

    @state()
    public config?: Config;

    @state()
    public brand?: CurrentBrand;

    constructor() {
        super();

        this.addController(new BrandContextController(this));
        this[configContext] = new ConfigContextController(this);
        this[modalController] = new ModalOrchestrationController(this);
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
