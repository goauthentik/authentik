import { WizardCloseEvent } from "./events.js";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { formatCreateLabel, type NamedEntityElementConstructor } from "#elements/dialogs/shared";
import { navigate } from "#elements/router/core/navigation";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";

import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * @class AKFullPageWizard
 * @component ak-full-page-wizard
 *
 * Hosts a wizard as a full page rather than in a modal. Slot either an `<ak-wizard-steps>` or an
 * `<ak-wizard>` into it; the wizard omits its own header in favor of the standard page header, and
 * its cancel/close/finish buttons navigate to {@linkcode returnURL} instead of dismissing a dialog.
 */
@customElement("ak-full-page-wizard")
export class AKFullPageWizard extends AKElement {
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

    @property({ type: String })
    public header?: string;

    @property({ type: String })
    public description?: string;

    @property({ type: String })
    public icon?: string;

    /**
     * Where to send the user when the wizard is cancelled or finished.
     */
    @property({ type: String, attribute: "return-url" })
    public returnURL = "/";

    @listen(WizardCloseEvent)
    protected closeListener = () => navigate(this.returnURL);

    public override willUpdate() {
        setPageDetails({
            header: this.header,
            description: this.description,
            icon: this.icon,
        });
    }

    protected override render() {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-full-page-wizard": AKFullPageWizard;
    }
}

/**
 * A helper function to render a link to the full-page wizard that creates a new **model**
 * instance; the full-page counterpart of {@linkcode ModalInvokerButton}.
 *
 * @param href The route of the wizard's page, e.g. `toAdminInterface("core/providers/new")`.
 * @param factory The wizard element constructor, used for the label.
 */
export function WizardLinkButton(
    href: string,
    factory: NamedEntityElementConstructor,
): SlottedTemplateResult {
    return html`<a class="pf-c-button pf-m-primary" href=${href}>${formatCreateLabel(factory)}</a>`;
}
