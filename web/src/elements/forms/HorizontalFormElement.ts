import { isControlElement } from "#elements/AkControlElement";
import { AKElement } from "#elements/Base";
import { AKFormGroup } from "#elements/forms/FormGroup";
import { isNameableElement } from "#elements/utils/inputs";

import { AKFormErrors, ErrorProp } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 *
 * Horizontal Form Element Container.
 *
 * This element provides the interface between elements of our forms and the
 * form itself.
 * @custom-element ak-form-element-horizontal
 */

/* TODO

 * 1. Replace the "probe upward for a parent object to event" with an event handler on the parent
 *    group.
 * 2. Updated() has a lot of that slug code again. Really, all you want is for the slug input object
 *    to update itself if its content seems to have been tracking some other key element.
 * 3. Updated() pushes the `name` field down to the children, as if that were necessary; why isn't
 *    it being written on-demand when the child is written? Because it's slotted... despite there
 *    being very few unique uses.
 */

@customElement("ak-form-element-horizontal")
export class HorizontalFormElement extends AKElement {
    static styles: CSSResult[] = [
        PFBase,
        PFForm,
        PFFormControl,
        css`
            .pf-c-form__group {
                display: grid;
                grid-template-columns:
                    var(--pf-c-form--m-horizontal__group-label--md--GridColumnWidth)
                    var(--pf-c-form--m-horizontal__group-control--md--GridColumnWidth);
            }
        `,
    ];

    //#region Properties

    /**
     * A unique ID to associate with the input and label.
     */
    @property({ type: String, reflect: false })
    public fieldID?: string;

    /**
     * The label for the input control
     * @property
     * @attribute
     * @deprecated Labels cannot associate with inputs across DOM roots. Use the slotted `label` element instead.
     */
    @property({ type: String })
    public label?: string;

    @property({ type: Boolean })
    public required?: boolean;

    @property({ attribute: false })
    public errorMessages?: ErrorProp[];

    #invalid = false;

    /* If this property changes, we want to make sure the parent control is "opened" so
     * that users can see the change.[1]
     */
    @property({ type: Boolean })
    set invalid(v: boolean) {
        this.#invalid = v;
        // check if we're in a form group, and expand that form group
        const parent = this.parentElement?.parentElement;

        if (parent instanceof AKFormGroup || parent instanceof HTMLDetailsElement) {
            parent.open = true;
        }
    }
    get invalid(): boolean {
        return this.#invalid;
    }

    @property({ type: String })
    public name?: string;

    //#endregion

    //#region Lifecycle

    public override firstUpdated(): void {
        this.updated();
    }

    /**
     * Ensure that all inputs have a name attribute.
     *
     * TODO: Swap with `HTMLElement.prototype.attachInternals`.
     */
    public override updated(): void {
        // If we don't have a name, we can't do anything.
        if (!this.name) return;

        for (const element of this.querySelectorAll("*")) {
            // Is this element capable of being named?
            if (!isControlElement(element) && !isNameableElement(element)) continue;
            // And does the element already match the name?
            if (element.getAttribute("name") === this.name) continue;

            element.setAttribute("name", this.name);
        }
    }

    //#endregion

    //#region Rendering

    render(): TemplateResult {
        this.updated();

        return html`<div class="pf-c-form__group" role="group">
            ${this.label
                ? html`<div class="pf-c-form__group-label">
                      ${AKLabel({ htmlFor: this.fieldID, required: this.required }, this.label)}
                  </div>`
                : nothing}
            <slot name="label"></slot>

            <div class="pf-c-form__group-control">
                <slot class="pf-c-form__horizontal-group"></slot>
                <div class="pf-c-form__horizontal-group">
                    ${AKFormErrors({ errors: this.errorMessages })}
                </div>
            </div>
        </div>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-element-horizontal": HorizontalFormElement;
    }
}
