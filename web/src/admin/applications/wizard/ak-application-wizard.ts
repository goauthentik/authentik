import "#admin/applications/wizard/ak-application-wizard-main";

import { AKModal } from "#elements/modals/ak-modal";
import { asInvoker } from "#elements/modals/utils";
import { SlottedTemplateResult } from "#elements/types";

import { WizardCloseEvent } from "#components/ak-wizard/events";

import { css, CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-application-wizard")
export class AkApplicationWizard extends AKModal {
    public static override styles: CSSResult[] = [
        ...super.styles,
        css`
            [part="main"] {
                display: block;
            }
        `,
    ];

    public static open = asInvoker(AkApplicationWizard);

    constructor() {
        super();

        this.addEventListener(WizardCloseEvent.eventName, this.closeListener);
    }

    protected renderCloseButton(): SlottedTemplateResult {
        return null;
    }

    render() {
        return html`<ak-application-wizard-main part="main"></ak-application-wizard-main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard": AkApplicationWizard;
    }
}
