import { AKElement } from "#elements/Base";
import { formatCreateLabel, type NamedEntityElementConstructor } from "#elements/dialogs/shared";
import { navigate } from "#elements/router/core/navigation";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";

import { html } from "lit";
import { property } from "lit/decorators.js";

/**
 * @class AKFullPage
 *   The common ground of the full-page hosts: something that would otherwise be shown in a modal —
 *   a wizard or a form — is instead given a route of its own. The host renders the standard page
 *   header, and knows where to send the user once the thing it hosts is done or dismissed.
 * @see {@linkcode AKFullPageWizard} for wizards.
 * @see {@linkcode AKFullPageForm} for forms.
 */
export abstract class AKFullPage extends AKElement {
    @property({ type: String })
    public header?: string;

    @property({ type: String })
    public description?: string;

    @property({ type: String })
    public icon?: string;

    /**
     * Where to send the user when the hosted wizard or form is finished or dismissed.
     */
    @property({ type: String, attribute: "return-url" })
    public returnURL = "/";

    /**
     * Leave the page, returning to wherever this was started from.
     */
    protected returnToOrigin = (): void => navigate(this.returnURL);

    public override willUpdate() {
        setPageDetails({
            header: this.header,
            description: this.description,
            icon: this.icon,
        });
    }
}

/**
 * A helper function to render a link to a full-page wizard or form that creates a new **model**
 * instance; the full-page counterpart of {@linkcode ModalInvokerButton}.
 *
 * @param href The route of the page, e.g. `toAdminInterface("core/providers/new")`.
 * @param factory The wizard or form element constructor, used for the label.
 */
export function CreateLinkButton(
    href: string,
    factory: NamedEntityElementConstructor,
): SlottedTemplateResult {
    return html`<a class="pf-c-button pf-m-primary" href=${href}>${formatCreateLabel(factory)}</a>`;
}
