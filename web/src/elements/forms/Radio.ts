import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface RadioOption<T> {
    label: string;
    description?: TemplateResult;
    default: boolean;
    value: T;
}

@customElement("ak-radio")
export class Radio<T> extends AKElement {
    @property({ attribute: false })
    options: RadioOption<T>[] = [];

    @property()
    name = "";

    @property({ attribute: false })
    value?: T;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFRadio,
            PFForm,
            css`
                .pf-c-form__group-control {
                    padding-top: calc(
                        var(--pf-c-form--m-horizontal__group-label--md--PaddingTop) * 1.3
                    );
                }
            `,
        ];
    }

    render(): TemplateResult {
        if (!this.value) {
            const def = this.options.filter((opt) => opt.default);
            if (def.length > 0) {
                this.value = def[0].value;
            }
        }
        return html`<div class="pf-c-form__group-control pf-m-stack">
            ${this.options.map((opt) => {
                const elId = `${this.name}-${opt.value}`;
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="${this.name}"
                        id=${elId}
                        @change=${() => {
                            this.value = opt.value;
                            this.dispatchEvent(
                                new CustomEvent("change", {
                                    bubbles: true,
                                    composed: true,
                                    detail: opt.value,
                                }),
                            );
                        }}
                        .checked=${opt.value === this.value}
                    />
                    <label class="pf-c-radio__label" for=${elId}>${opt.label}</label>
                    ${opt.description
                        ? html`<span class="pf-c-radio__description">${opt.description}</span>`
                        : html``}
                </div>`;
            })}
        </div>`;
    }
}
