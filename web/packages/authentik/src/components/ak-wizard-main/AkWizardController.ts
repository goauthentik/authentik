import { type ReactiveController } from "lit";

import { type AkWizard, type WizardNavCommand } from "./types";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isCustomEvent = (v: any): v is CustomEvent =>
    v instanceof CustomEvent && "detail" in v;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isNavEvent = (v: any): v is CustomEvent<WizardNavCommand> =>
    isCustomEvent(v) && "command" in v.detail;

/**
 * AkWizardController
 *
 * A ReactiveController that plugs into any wizard and provides a somewhat more convenient API for
 * interacting with that wizard. It expects three different events from the wizard frame, each of
 * which has a corresponding method that then forwards the necessary information to the host:
 *
 * - nav: A request to navigate to different step. Calls the host's `handleNav()` with the requested
     step number.
 * - update: A request to update the content of the current step. Forwarded to the host's
 *   `handleUpdate()` method.
 * - close: A request to end the wizard interaction. Forwarded to the host's `close()` method.
 *
 */

export class AkWizardController<Data> implements ReactiveController {
    private host: AkWizard<Data>;

    constructor(host: AkWizard<Data>) {
        this.host = host;
        this.handleNavRequest = this.handleNavRequest.bind(this);
        this.handleUpdateRequest = this.handleUpdateRequest.bind(this);
        host.addController(this);
    }

    get maxStep() {
        return this.host.steps.length - 1;
    }

    get nextStep() {
        return this.host.currentStep < this.maxStep ? this.host.currentStep + 1 : undefined;
    }

    get backStep() {
        return this.host.currentStep > 0 ? this.host.currentStep - 1 : undefined;
    }

    get step() {
        return this.host.steps[this.host.currentStep];
    }

    hostConnected() {
        this.host.addEventListener("ak-wizard-nav", this.handleNavRequest);
        this.host.addEventListener("ak-wizard-update", this.handleUpdateRequest);
        this.host.addEventListener("ak-wizard-closed", this.handleCloseRequest);
    }

    hostDisconnected() {
        this.host.removeEventListener("ak-wizard-nav", this.handleNavRequest);
        this.host.removeEventListener("ak-wizard-update", this.handleUpdateRequest);
        this.host.removeEventListener("ak-wizard-closed", this.handleCloseRequest);
    }

    handleNavRequest(event: Event) {
        if (!isNavEvent(event)) {
            throw new Error(`Unexpected event received by nav handler: ${event}`);
        }

        if (event.detail.command === "close") {
            this.host.close();
            return;
        }

        const navigate = (): number | undefined => {
            switch (event.detail.command) {
                case "next":
                    return this.nextStep;
                case "back":
                    return this.backStep;
                case "goto":
                    return event.detail.step;
                default:
                    throw new Error(
                        `Unrecognized command passed to ak-wizard-controller:handleNavRequest: ${event.detail.command}`,
                    );
            }
        };

        this.host.handleNav(navigate());
    }

    handleUpdateRequest(event: Event) {
        if (!isCustomEvent(event)) {
            throw new Error(`Unexpected event received by nav handler: ${event}`);
        }
        this.host.handleUpdate(event.detail);
    }

    handleCloseRequest() {
        this.host.close();
    }
}
