import { WizardCloseEvent } from "./events.js";

import { listen } from "#elements/decorators/listen";

import { AKFullPage } from "#components/ak-full-page";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

/**
 * @class AKFullPageWizard
 * @component ak-full-page-wizard
 *
 * Hosts a wizard as a full page rather than in a modal. Slot either an `<ak-wizard-steps>` or an
 * `<ak-wizard>` into it; the wizard omits its own header in favor of the standard page header, and
 * its cancel/close/finish buttons navigate to {@linkcode returnURL} instead of dismissing a dialog.
 */
@customElement("ak-full-page-wizard")
export class AKFullPageWizard extends AKFullPage {
    public static styles = [
        css`
            :host {
                /* Stand in for the dialog sizing the wizards otherwise inherit. */
                --ak-c-dialog--AspectRatioHeight: 100%;
                --ak-c-dialog--MaxHeight: 100%;

                display: flex;
                flex: 1 1 auto;
                flex-flow: column;
                min-height: 0;
            }

            ::slotted(*),
            :host > * {
                flex: 1 1 auto;
                min-height: 0;
            }
        `,
    ];

    @listen(WizardCloseEvent)
    protected closeListener = this.returnToOrigin;

    protected override render() {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-full-page-wizard": AKFullPageWizard;
    }
}
