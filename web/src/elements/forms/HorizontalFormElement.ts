import { convertToSlug } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import { FormGroup } from "@goauthentik/elements/forms/FormGroup";

import { msg } from "@lit/localize";
import { CSSResult, css } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * @custom-element ak-form-element-horizontal
 */

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
    errorMessages: string[] = [];

    @property({ type: Boolean })
    slugMode = false;

    _invalid = false;

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
                    input.value = convertToSlug(input.value);
                });
            });
        }
        this.querySelectorAll("*").forEach((input) => {
            switch (input.tagName.toLowerCase()) {
                case "input":
                case "textarea":
                case "select":
                case "ak-codemirror":
                case "ak-chip-group":
                case "ak-search-select":
                case "ak-radio":
                    input.setAttribute("name", this.name);
                    break;
                default:
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
                        return html`<p class="pf-c-form__helper-text pf-m-error" aria-live="polite">
                            ${message}
                        </p>`;
                    })}
                </div>
            </div>
        </div>`;
    }
}
