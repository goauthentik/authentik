import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, queryAll } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

type CheckboxKv = { name: string; label: string | TemplateResult };
type CheckboxPr = [string, string | TemplateResult];
export type CheckboxPair = CheckboxKv | CheckboxPr;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isCheckboxPr = (t: any): t is CheckboxPr => Array.isArray(t);
function* kvToPairs(items: CheckboxPair[]): Iterable<CheckboxPr> {
    for (const item of items) {
        yield isCheckboxPr(item) ? item : [item.name, item.label];
    }
}

const AkElementWithCustomEvents = CustomEmitterElement(AKElement);

/**
 * @element ak-checkbox-group
 *
 * @class CheckboxGroup
 *
 * @description
 * CheckboxGroup renders a collection of checkboxes in a linear list. Multiple
 * checkboxes may be picked.
 *
 * @attr {options} - An array of either `[string, string | TemplateResult]` or
 *     `{ name: string, label: string | TemplateResult }`. The first value or
 *     `name` field must be a valid HTML identifier compatible with the HTML
 *     `name` attribute.
 *
 * @attr {value} - An array of `name` values corresponding to the options that
 *     are selected when the element is rendered.
 *
 * @attr {name} - The name of this element as it will appear in any <form>
 *     transaction
 *
 * @attr {required} - If true, and if name is set, and no values are chosen,
 *     will automatically fail a form `submit` event, providing a warning
 *     message for any labeling. Note: if `name` is not set, this has no effect,
 *     and a warn() will appear on the console.
 *
 * @event {input} - Fired when the component's value has changed. Current value
 *     as an array of `name` will be in the `Event.detail` field.
 *
 * @event {change} - Fired when the component's value has changed. Current value
 *     as an array of `name` will be in the `Event.detail` field.
 *
 * @csspart checkbox - The div containing the checkbox item and the label
 * @csspart label - the label
 * @csspart input - the input item
 * @csspart checkbox-group - the wrapper div with flexbox control
 *
 * ## Bigger hit area
 *
 * Providing properly formatted names for selections allows the element to
 * associate the label with the event, so the entire horizontal area from
 * checkbox to end-of-label will be the hit area.
 *
 * ## FormAssociated compliance
 *
 * If a <form> component is a parent, this component will correctly send its
 * values to the form for `x-form-encoded` data; multiples will appear in the
 * form of `name=value1&name=value2` format, and must be unpacked into an array
 * correctly on the server side according to the CGI (common gateway interface)
 * protocol.
 *
 */

@customElement("ak-checkbox-group")
export class CheckboxGroup extends AkElementWithCustomEvents {
    static get styles() {
        return [PFBase, PFFlex, PFCheck];
    }

    static get formAssociated() {
        return true;
    }

    @property({ type: Array })
    options: CheckboxPair[] = [];

    @property({ type: Array })
    value: string[] = [];

    @property({ type: String })
    name?: string;

    @property({ type: Boolean })
    required = false;

    @queryAll('input[type="checkbox"]')
    checkboxes!: NodeListOf<HTMLInputElement>;

    internals?: ElementInternals;

    get json() {
        return this.value;
    }

    private get formValue() {
        if (this.name === undefined) {
            throw new Error("This cannot be called without having the name set.");
        }
        const name = this.name;
        const entries = new FormData();
        this.value.forEach((v) => entries.append(name, v));
        return entries;
    }

    constructor() {
        super();
        this.onClick = this.onClick.bind(this);
        this.dataset.akControl = "true";
    }

    onClick(ev: Event) {
        ev.stopPropagation();
        this.value = Array.from(this.checkboxes)
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.name);
        this.dispatchCustomEvent("change", this.value);
        this.dispatchCustomEvent("input", this.value);
        if (this.internals) {
            this.internals.setValidity({});
            if (this.required && this.value.length === 0) {
                this.internals.setValidity(
                    {
                        valueMissing: true,
                    },
                    msg("A selection is required"),
                    this,
                );
            }
            this.internals.setFormValue(this.formValue);
        }
    }

    connectedCallback() {
        super.connectedCallback();
        if (this.name && !this.internals) {
            this.internals = this.attachInternals();
        }
        if (this.internals && this.name) {
            this.internals.ariaRequired = this.required ? "true" : "false";
        }
        if (this.required && !this.internals) {
            console.warn(
                "Setting `required` on ak-checkbox-group has no effect when the `name` attribute is unset",
            );
        }
        // These are necessary to prevent the input components' own events from
        // leaking out. This helps maintain the illusion that this component
        // behaves similarly to the multiple selection behavior of, well,
        // <select multiple>.
        this.addEventListener("input", (ev) => {
            ev.stopPropagation();
        });
        this.addEventListener("change", (ev) => {
            ev.stopPropagation();
        });
    }

    render() {
        const renderOne = ([name, label]: CheckboxPr) => {
            const selected = this.value.includes(name);
            const blockFwd = (e: Event) => {
                e.stopImmediatePropagation();
            };

            return html` <div
                part="checkbox"
                class="pf-l-flex__item pf-c-check"
                @click=${this.onClick}
            >
                <input
                    part="input"
                    @change=${blockFwd}
                    @input=${blockFwd}
                    name="${name}"
                    class="pf-c-check__input"
                    type="checkbox"
                    ?checked=${selected}
                    id="ak-check-${name}"
                />
                <label part="label" class="pf-c-check__label" for="ak-check-${name}"
                    >${label}</label
                >
            </div>`;
        };

        return html`<div part="checkbox-group" class="pf-l-flex pf-m-space-items-sm pf-m-column">
            ${map(kvToPairs(this.options), renderOne)}
        </div>`;
    }
}
