import "./ak-application-wizard-main.js";

import { ModalButton } from "#elements/buttons/ModalButton";
import { bound } from "#elements/decorators/bound";

import { WizardCloseEvent } from "#components/ak-wizard/events";

import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-application-wizard")
export class AkApplicationWizard extends ModalButton {
    constructor() {
        super();
        this.addEventListener(WizardCloseEvent.eventName, this.onCloseEvent);
    }

    @bound
    onCloseEvent(ev: WizardCloseEvent) {
        ev.stopPropagation();
        this.open = false;
    }

    renderModalInner() {
        return html` <ak-application-wizard-main> </ak-application-wizard-main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard": AkApplicationWizard;
    }
}
