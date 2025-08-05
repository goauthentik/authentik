import { AKElement } from "#elements/Base";
import { CustomEmitterElement } from "#elements/utils/eventEmitter";

import { IDGenerator } from "@goauthentik/core/id";

import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface RadioOption<T> {
    label: string;
    description?: TemplateResult;
    className?: string;
    default?: boolean;
    value: T;
    disabled?: boolean;
}

@customElement("ak-radio")
export class Radio<T> extends CustomEmitterElement(AKElement) {
    @property({ attribute: false })
    public options: RadioOption<T>[] = [];

    @property()
    public name = "";

    @property({ attribute: false })
    public value?: T;

    #fieldID: string = this.name || IDGenerator.randomID();

    static styles: CSSResult[] = [
        PFBase,
        PFRadio,
        PFForm,
        css`
            .pf-c-form__group-control {
                padding-top: calc(
                    var(--pf-c-form--m-horizontal__group-label--md--PaddingTop) * 1.3
                );
            }
            .pf-c-radio label,
            .pf-c-radio span {
                user-select: none;
            }

            .pf-c-radio__description {
                text-wrap: balance;
            }
        `,
    ];

    // Set the value if it's not set already. Property changes inside the `willUpdate()` method do
    // not trigger an element update.
    willUpdate() {
        if (!this.value) {
            const maybeDefault = this.options.filter((opt) => opt.default);
            if (maybeDefault.length > 0) {
                this.value = maybeDefault[0].value;
            }
        }
    }

    // When a user clicks on `type="radio"`, *two* events happen in rapid succession: the original
    // radio loses its setting, and the selected radio gains its setting. We want radio buttons to
    // present a unified event interface, so we prevent the event from triggering if the value is
    // already set.
    #buildChangeListener = (option: RadioOption<T>) => {
        return (ev: Event) => {
            // This is a controlled input. Stop the native event from escaping or affecting the
            // value. We'll do that ourselves.
            ev.stopPropagation();

            if (option.disabled) {
                return;
            }

            this.value = option.value;

            this.dispatchCustomEvent("change", { value: option.value });
            this.dispatchCustomEvent("input", { value: option.value });
        };
    };

    #renderRadio = (option: RadioOption<T>, index: number) => {
        const id = `${this.#fieldID}-${index}`;

        const changeListener = this.#buildChangeListener(option);

        return html`<div class="pf-c-radio" @click=${changeListener}>
            <input
                class="pf-c-radio__input"
                type="radio"
                name="${this.name}"
                aria-label=${option.label}
                id=${id}
                .checked=${option.value === this.value}
                .disabled=${option.disabled}
            />
            <label class="pf-c-radio__label ${option.className ?? ""}" for=${id}
                >${option.label}</label
            >
            ${option.description
                ? html`<span class="pf-c-radio__description">${option.description}</span>`
                : nothing}
        </div>`;
    };

    render() {
        return html`<div class="pf-c-form__group-control pf-m-stack">
            ${map(this.options, this.#renderRadio)}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-radio": Radio<unknown>;
    }
}

export default Radio;
