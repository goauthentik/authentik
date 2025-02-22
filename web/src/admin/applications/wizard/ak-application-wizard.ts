import { WizardCloseEvent } from "@goauthentik/components/ak-wizard/events.js";
import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import { bound } from "@goauthentik/elements/decorators/bound.js";

import { html } from "lit";
import { customElement } from "lit/decorators.js";

import "./ak-application-wizard-main.js";

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
