import "#admin/applications/wizard/ak-application-wizard-main";

import { AKModal } from "#elements/modals/ak-modal";
import { renderDialog } from "#elements/modals/utils";
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

    public static open = (event?: Event) => {
        const ownerDocument =
            event?.target instanceof HTMLElement ? event.target.ownerDocument : document;

        const tagName = window.customElements.getName(AkApplicationWizard);

        if (!tagName) {
            throw new TypeError("Custom element is not defined");
        }

        const modal = ownerDocument.createElement(tagName);

        return renderDialog(modal, {
            ownerDocument,
        });
    };

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
