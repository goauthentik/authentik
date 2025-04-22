import {
    appendStyleSheet,
    createStyleSheetUnsafe,
    resolveStyleSheetParent,
} from "@goauthentik/common/stylesheets";
import { UIConfig } from "@goauthentik/common/ui/config";
import { AKElement, AKElementInit } from "@goauthentik/elements/Base";
import { ModalOrchestrationController } from "@goauthentik/elements/controllers/ModalOrchestrationController.js";
import { BrandController } from "@goauthentik/elements/mixins/brand";
import { ConfigController } from "@goauthentik/elements/mixins/config";

import { state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { Config, CurrentBrand, SessionUser } from "@goauthentik/api";

/**
 * A UI interface representing an entry point within the application.
 */
export abstract class InterfaceElement extends AKElement {
    static readonly PFBaseStyleSheet = createStyleSheetUnsafe(PFBase);

    @state()
    session?: SessionUser;

    @state()
    uiConfig?: UIConfig;

    @state()
    config?: Config;

    @state()
    brand?: CurrentBrand;

    constructor({ styleParents = [], ...init }: AKElementInit = {}) {
        const styleParent = resolveStyleSheetParent(document);

        super({
            ...init,
            styleParents: [styleParent, ...styleParents],
        });

        this.dataset.akInterfaceRoot = this.tagName.toLowerCase();

        appendStyleSheet(InterfaceElement.PFBaseStyleSheet, styleParent);

        this.registerControllers();
    }

    /**
     * Register all controllers for this interface element.
     *
     * Override this method to register additional controllers,
     * or opt-out of the default controllers.
     */
    public registerControllers() {
        new BrandController(this);
        new ConfigController(this);
        new ModalOrchestrationController(this);
    }
}
