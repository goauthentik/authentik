import { AKElement } from "@goauthentik/elements/Base";
import { FormGroup } from "@goauthentik/elements/forms/FormGroup";
import { formatAsSlug } from "@goauthentik/elements/router";

import { msg, str } from "@lit/localize";
import { CSSResult, css } from "lit";
import { TemplateResult, html } from "lit";
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
 * 4. There is some very specific use-case around the `writeOnly` boolean; this seems to be a case
 *    where the field isn't available for the user to view unless they explicitly request to be able
 *    to see the content; otherwise, a dead password field is shown. There are 10 uses of this
 *    feature.
 *
 */

const isAkControl = (el: unknown): boolean =>
    el instanceof HTMLElement &&
    "dataset" in el &&
    el.dataset instanceof DOMStringMap &&
    "akControl" in el.dataset;

const nameables = new Set([
    "input",
    "textarea",
    "select",
    "ak-codemirror",
    "ak-chip-group",
    "ak-search-select",
    "ak-radio",
]);

@customElement("ak-form-element-horizontal")
export class HorizontalFormElement extends AKElement {
    static get styles(): CSSResult[] {
        return [
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
                .pf-c-form__group-label {
                    padding-top: var(--pf-c-form--m-horizontal__group-label--md--PaddingTop);
                }
            `,
        ];
    }

    @property()
    label = "";

    @property({ type: Boolean })
    required = false;

    @property({ type: Boolean })
    writeOnly = false;

    @property({ type: Boolean })
    writeOnlyActivated = false;

    @property({ attribute: false })
    errorMessages: string[] | string[][] = [];

    @property({ type: Boolean })
    slugMode = false;

    _invalid = false;

    /* If this property changes, we want to make sure the parent control is "opened" so
     * that users can see the change.[1]
     */
    @property({ type: Boolean })
    set invalid(v: boolean) {
        this._invalid = v;
        // check if we're in a form group, and expand that form group
        const parent = this.parentElement?.parentElement;
        if (parent && "expanded" in parent) {
            (parent as FormGroup).expanded = true;
        }
    }
    get invalid(): boolean {
        return this._invalid;
    }

    @property()
    name = "";

    firstUpdated(): void {
        this.updated();
    }

    updated(): void {
        this.querySelectorAll<HTMLInputElement>("input[autofocus]").forEach((input) => {
            input.focus();
        });
        if (this.name === "slug" || this.slugMode) {
            this.querySelectorAll<HTMLInputElement>("input[type='text']").forEach((input) => {
                input.addEventListener("keyup", () => {
                    input.value = formatAsSlug(input.value);
                });
            });
        }
        this.querySelectorAll("*").forEach((input) => {
            if (isAkControl(input) && !input.getAttribute("name")) {
                input.setAttribute("name", this.name);
                // This is fine; writeOnly won't apply to anything built this way.
                return;
            }

            if (nameables.has(input.tagName.toLowerCase())) {
                input.setAttribute("name", this.name);
            } else {
                return;
            }

            if (this.writeOnly && !this.writeOnlyActivated) {
                const i = input as HTMLInputElement;
                i.setAttribute("hidden", "true");
                const handler = () => {
                    i.removeAttribute("hidden");
                    this.writeOnlyActivated = true;
                    i.parentElement?.removeEventListener("click", handler);
                };
                i.parentElement?.addEventListener("click", handler);
            }
        });
    }

    render(): TemplateResult {
        this.updated();
        return html`<div class="pf-c-form__group">
            <div class="pf-c-form__group-label">
                <label class="pf-c-form__label">
                    <span class="pf-c-form__label-text">${this.label}</span>
                    ${this.required
                        ? html`<span class="pf-c-form__label-required" aria-hidden="true">*</span>`
                        : html``}
                </label>
            </div>
            <div class="pf-c-form__group-control">
                ${this.writeOnly && !this.writeOnlyActivated
                    ? html`<div class="pf-c-form__horizontal-group">
                          <input
                              class="pf-c-form-control"
                              type="password"
                              disabled
                              value="**************"
                          />
                      </div>`
                    : html``}
                <slot class="pf-c-form__horizontal-group"></slot>
                <div class="pf-c-form__horizontal-group">
                    ${this.writeOnly
                        ? html`<p class="pf-c-form__helper-text" aria-live="polite">
                              ${msg("Click to change value")}
                          </p>`
                        : html``}
                    ${this.errorMessages.map((message) => {
                        if (message instanceof Object) {
                            return html`${Object.entries(message).map(([field, errMsg]) => {
                                return html`<p
                                    class="pf-c-form__helper-text pf-m-error"
                                    aria-live="polite"
                                >
                                    ${msg(str`${field}: ${errMsg}`)}
                                </p>`;
                            })}`;
                        }
                        return html`<p class="pf-c-form__helper-text pf-m-error" aria-live="polite">
                            ${message}
                        </p>`;
                    })}
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-element-horizontal": HorizontalFormElement;
    }
}
