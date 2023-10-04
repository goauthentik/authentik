import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { randomId } from "../utils/randomId";

export interface RadioOption<T> {
    label: string;
    description?: TemplateResult;
    default: boolean;
    value: T;
}

@customElement("ak-radio")
export class Radio<T> extends CustomEmitterElement(AKElement) {
    @property({ attribute: false })
    options: RadioOption<T>[] = [];

    @property()
    name = "";

    @property({ attribute: false })
    value?: T;

    internalId: string;

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
                .pf-c-radio label,
                .pf-c-radio span {
                    user-select: none;
                }
            `,
        ];
    }

    constructor() {
        super();
        this.renderRadio = this.renderRadio.bind(this);
        this.buildChangeHandler = this.buildChangeHandler.bind(this);
        this.internalId = this.name || `radio-${randomId(8)}`;
    }

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
    buildChangeHandler(option: RadioOption<T>) {
        return (ev: Event) => {
            // This is a controlled input. Stop the native event from escaping or affecting the
            // value.  We'll do that ourselves.
            ev.stopPropagation();
            this.value = option.value;
            this.dispatchCustomEvent("change", { value: option.value });
            this.dispatchCustomEvent("input", { value: option.value });
        };
    }

    renderRadio(option: RadioOption<T>, index: number) {
        const elId = `${this.internalId}-${index}`;
        const handler = this.buildChangeHandler(option);
        return html`<div class="pf-c-radio" @click=${handler}>
            <input
                class="pf-c-radio__input"
                type="radio"
                name="${this.name}"
                id=${elId}
                .checked=${option.value === this.value}
            />
            <label class="pf-c-radio__label" for=${elId}>${option.label}</label>
            ${option.description
                ? html`<span class="pf-c-radio__description">${option.description}</span>`
                : nothing}
        </div>`;
    }

    render() {
        return html`<div class="pf-c-form__group-control pf-m-stack">
            ${map(this.options, this.renderRadio)}
        </div>`;
    }
}

export default Radio;
