import { globalAK } from "#common/global";
import { applyDocumentTheme } from "#common/theme";
import { AKElement } from "#elements/Base";
import { BrandingContextController } from "#elements/controllers/BrandContextController";
import { ConfigContextController } from "#elements/controllers/ConfigContextController";
import { ModalOrchestrationController } from "#elements/controllers/ModalOrchestrationController";
import { WithAuthentikConfig } from "#elements/mixins/config";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * The base interface element for the application.
 */
export abstract class Interface extends WithAuthentikConfig(AKElement) {
    static styles = [PFBase];

    constructor() {
        super();

        const { config, brand } = globalAK();

        applyDocumentTheme(brand.uiTheme);

        this.addController(new ConfigContextController(this, config));
        this.addController(new BrandingContextController(this, brand));
        this.addController(new ModalOrchestrationController());
    }

    public connectedCallback(): void {
        super.connectedCallback();
        this.dataset.akInterfaceRoot = this.tagName.toLowerCase();
    }
}
