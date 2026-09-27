import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { listen } from "#elements/decorators/listen";
import { AKFormSubmittedEvent } from "#elements/forms/events";
import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";
import { findSlottedInstance } from "#elements/utils/slots";

import { AKFullPage } from "#components/ak-full-page";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, state } from "lit/decorators.js";

/**
 * @class AKFullPageForm
 * @component ak-full-page-form
 *
 * Hosts a form as a full page rather than in a modal. Slot the form into it:
 *
 * ```html
 * <ak-full-page-form header=${msg("New Rule")} return-url=${toAdminInterface("requests/rules")}>
 *     <ak-request-rule-form></ak-request-rule-form>
 * </ak-full-page-form>
 * ```
 *
 * Being slotted, the form leaves its header and actions to this host, exactly as it does inside
 * {@linkcode AKModal} — the header becomes the standard page header, and the actions are rendered
 * into the page footer alongside a cancel link. A successful submission returns the user to
 * {@linkcode returnURL}.
 */
@customElement("ak-full-page-form")
export class AKFullPageForm extends AKFullPage {
    public static styles = [
        PFButton,
        PFCard,
        PFForm,
        PFPage,
        css`
            .pf-c-card__footer {
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--md);
            }

            /* The form wraps its actions in a footer of its own, which this host supplies. */
            .pf-c-card__footer > [part="form-actions"] {
                display: contents;
            }
        `,
    ];

    protected readonly formSlot: HTMLSlotElement;

    @state()
    protected slottedForm: Form<unknown, unknown> | null = null;

    //#region Listeners

    @listen(AKFormSubmittedEvent)
    protected submittedListener = this.returnToOrigin;

    protected slotChangeListener = () => {
        const form = findSlottedInstance(Form, this.formSlot);

        if (!form) return;

        // Forms don't render until they're told they're on screen.
        form.visible = true;

        this.slottedForm = form;
    };

    //#endregion

    //#region Lifecycle

    public constructor() {
        super();

        this.formSlot = this.ownerDocument.createElement("slot");
        this.formSlot.addEventListener("slotchange", this.slotChangeListener);
    }

    //#endregion

    //#region Rendering

    protected renderActions(): SlottedTemplateResult {
        const { slottedForm } = this;

        if (!slottedForm) return null;

        const cancelButton = slottedForm.cancelable
            ? html`<a class="pf-c-button pf-m-link" href=${this.returnURL}
                  >${slottedForm.cancelButtonLabel ?? msg("Cancel")}</a
              >`
            : null;

        return html`<footer class="pf-c-card__footer" part="actions">
            ${cancelButton}${slottedForm.renderActions(true)}
        </footer>`;
    }

    protected override render() {
        return html`<main class="pf-c-page__main-section pf-m-no-padding-mobile">
            <div class="pf-c-card">
                <div class="pf-c-card__body">${this.formSlot}</div>
                ${this.renderActions()}
            </div>
        </main>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-full-page-form": AKFullPageForm;
    }
}
