import { AkControlElement, isControlElement } from "#elements/AkControlElement";
import { AKElement } from "#elements/Base";
import { isNameableElement, NamedElement } from "#elements/utils/inputs";

import { AKFormErrors, ErrorProp } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { css, CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

/**
 * Horizontal Form Element Container.
 *
 * This element provides the interface between elements of our forms and the
 * form itself.
 * @custom-element ak-form-element-horizontal
 *
 * @TODO
 * 1. Updated() has a lot of that slug code again. Really, all you want is for the slug input object
 *    to update itself if its content seems to have been tracking some other key element.
 * 2. Updated() pushes the `name` field down to the children, as if that were necessary; why isn't
 *    it being written on-demand when the child is written? Because it's slotted... despite there
 *    being very few unique uses.
 */
@customElement("ak-form-element-horizontal")
export class HorizontalFormElement extends AKElement {
    static styles: CSSResult[] = [
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

    @property({ type: Boolean, reflect: false })
    public required?: boolean;

    @property({ attribute: false })
    public errorMessages?: ErrorProp[];

    @property({ type: String })
    public name?: string;

    //#endregion

    #controlledElement: AkControlElement | NamedElement | null = null;

    /**
     * The element that should be focused when the form is submitted.
     */
    public get focusTarget(): AkControlElement | NamedElement<HTMLElement> | null {
        if (!(this.#controlledElement instanceof HTMLElement)) {
            return null;
        }

        if (!this.#controlledElement.checkVisibility()) return null;

        return this.#controlledElement;
    }

    //#region Lifecycle

    public override firstUpdated(): void {
        this.#synchronizeAttributes();
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        if (changedProperties.has("errorMessages") && this.#controlledElement) {
            this.#controlledElement.setAttribute(
                "aria-invalid",
                this.errorMessages?.length ? "true" : "false",
            );
        }
    }

    /**
     * Ensure that all inputs have a name attribute.
     *
     * TODO: Swap with `HTMLElement.prototype.attachInternals`.
     */
    #synchronizeAttributes(): void {
        // If we don't have a name, we can't do anything.
        if (!this.name) return;

        for (const element of this.querySelectorAll("*")) {
            // Is this element capable of being named?
            if (!isControlElement(element) && !isNameableElement(element)) continue;

            this.#controlledElement = element;

            if (element.getAttribute("name") !== this.name) {
                element.setAttribute("name", this.name);
            }

            break;
        }
    }

    //#endregion

    //#region Rendering

    render(): TemplateResult {
        this.#synchronizeAttributes();

        return html`<div class="pf-c-form__group">
            ${this.label
                ? html`
                      ${AKLabel(
                          {
                              className: "pf-c-form__group-label",
                              htmlFor: this.fieldID,
                              required: this.required,
                          },
                          this.label,
                      )}
                  </div>`
                : html`<slot name="label"></slot>`}

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
