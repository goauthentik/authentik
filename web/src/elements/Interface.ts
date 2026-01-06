import { globalAK } from "#common/global";
import { applyDocumentTheme, createUIThemeEffect } from "#common/theme";

import { AKElement } from "#elements/Base";
import { BrandingContextController } from "#elements/controllers/BrandContextController";
import { ConfigContextController } from "#elements/controllers/ConfigContextController";
import { ContextControllerRegistry } from "#elements/controllers/ContextControllerRegistry";
import { LocaleContextController } from "#elements/controllers/LocaleContextController";
import { ModalOrchestrationController } from "#elements/controllers/ModalOrchestrationController";
import { ReactiveContextController } from "#elements/types";

import { Context, ContextType } from "@lit/context";
import { ReactiveController } from "lit";

/**
 * The base interface element for the application.
 */
export abstract class Interface extends AKElement {
    constructor() {
        super();

        const { config, brand, locale } = globalAK();

        createUIThemeEffect(applyDocumentTheme);

        this.addController(new LocaleContextController(this, locale));
        this.addController(new ConfigContextController(this, config));
        this.addController(new BrandingContextController(this, brand));
        this.addController(new ModalOrchestrationController());
    }

    public override addController(
        controller: ReactiveController,
        registryKey?: ContextType<Context<unknown, unknown>>,
    ): void {
        super.addController(controller);

        if (registryKey) {
            ContextControllerRegistry.set(registryKey, controller as ReactiveContextController);
        }
    }

    public connectedCallback(): void {
        super.connectedCallback();
        this.dataset.testId = "interface-root";
    }
}
