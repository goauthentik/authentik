import { customElement, LitElement, CSSResult, property, css } from "lit-element";
import { TemplateResult, html } from "lit-html";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import AKGlobal from "../../authentik.css";
import { t } from "@lingui/macro";

@customElement("ak-form-element-horizontal")
export class HorizontalFormElement extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFForm,
            PFFormControl,
            AKGlobal,
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

    @property()
    errorMessage = "";

    @property({ type: Boolean })
    invalid = false;

    @property()
    name = "";

    updated(): void {
        this.querySelectorAll<HTMLInputElement>("input[autofocus]").forEach((input) => {
            input.focus();
        });
        this.querySelectorAll("*").forEach((input) => {
            switch (input.tagName.toLowerCase()) {
                case "input":
                case "textarea":
                case "select":
                case "ak-codemirror":
                case "ak-chip-group":
                    (input as HTMLInputElement).name = this.name;
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
                              ${t`Click to change value`}
                          </p>`
                        : html``}
                    ${this.invalid
                        ? html`<p class="pf-c-form__helper-text pf-m-error" aria-live="polite">
                              ${this.errorMessage}
                          </p>`
                        : html``}
                </div>
            </div>
        </div>`;
    }
}
