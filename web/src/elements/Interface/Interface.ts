import {
    appendStyleSheet,
    createStyleSheetUnsafe,
    resolveStyleSheetParent,
} from "@goauthentik/common/stylesheets";
import { ThemedElement } from "@goauthentik/common/theme";
import { UIConfig } from "@goauthentik/common/ui/config";
import { AKElement } from "@goauthentik/elements/Base";
import { VersionContextController } from "@goauthentik/elements/Interface/VersionContextController";
import { ModalOrchestrationController } from "@goauthentik/elements/controllers/ModalOrchestrationController.js";

import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { Config, CurrentBrand, LicenseSummary, Version } from "@goauthentik/api";

import { BrandContextController } from "./BrandContextController";
import { ConfigContextController } from "./ConfigContextController";
import { EnterpriseContextController } from "./EnterpriseContextController";

const configContext = Symbol("configContext");
const modalController = Symbol("modalController");
const versionContext = Symbol("versionContext");

export abstract class Interface extends AKElement implements ThemedElement {
    protected static readonly PFBaseStyleSheet = createStyleSheetUnsafe(PFBase);

    [configContext]: ConfigContextController;

    [modalController]: ModalOrchestrationController;

    @state()
    public config?: Config;

    @state()
    public brand?: CurrentBrand;

    constructor() {
        super();
        const styleParent = resolveStyleSheetParent(document);

        this.dataset.akInterfaceRoot = this.tagName.toLowerCase();

        appendStyleSheet(styleParent, Interface.PFBaseStyleSheet);

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
