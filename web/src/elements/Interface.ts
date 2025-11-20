import {
    createContrastPreferenceEffect,
    createMotionPreferenceEffect,
    createTransparencyPreferenceEffect,
} from "#common/a11y";
import { globalAK } from "#common/global";
import { applyDocumentTheme, createUIThemeEffect } from "#common/theme";

import { AKElement } from "#elements/Base";
import { BrandingContextController } from "#elements/controllers/BrandContextController";
import { ConfigContextController } from "#elements/controllers/ConfigContextController";
import { ModalOrchestrationController } from "#elements/controllers/ModalOrchestrationController";

/**
 * The base interface element for the application.
 */
export abstract class Interface extends AKElement {
    constructor() {
        super();

        const { config, brand } = globalAK();

        createUIThemeEffect(applyDocumentTheme);

        this.addController(new ConfigContextController(this, config));
        this.addController(new BrandingContextController(this, brand));
        this.addController(new ModalOrchestrationController());

        createMotionPreferenceEffect();
        createContrastPreferenceEffect();
        createTransparencyPreferenceEffect();
    }

    public connectedCallback(): void {
        super.connectedCallback();
        this.dataset.testId = "interface-root";
    }
}
