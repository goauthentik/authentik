import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { map } from "lit/directives/map.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

type Pair = [string, string];

const selectStyles = css`
    select[multiple] {
        min-height: 15rem;
    }
`;

/**
 * Horizontal layout control with a multi-select.
 *
 * @part select - The select itself, to override the height specified above.
 */
@customElement("ak-multi-select")
export class AkMultiSelect extends AKElement {
    constructor() {
        super();
        this.dataset.akControl = "true";
    }

    static get styles() {
        return [PFBase, PFForm, PFFormControl, selectStyles];
    }

    /**
     * The [name] attribute, which is also distributed to the layout manager and the input control.
     */
    @property({ type: String })
    name!: string;

    /**
     * The text label to display on the control
     */
    @property({ type: String })
    label = "";

    /**
     * The values to be displayed in the select. The format is [Value, Label], where the label is
     * what will be displayed.
     */
    @property({ attribute: false })
    options: Pair[] = [];

    /**
     * If true, at least one object must be selected
     */
    @property({ type: Boolean })
    required = false;

    /**
     * Supporting a simple help string
     */
    @property({ type: String })
    help = "";

    /**
     * For more complex help instructions, provide a template result.
     */
    @property({ type: Object })
    bighelp!: TemplateResult | TemplateResult[];

    /**
     * An array of strings representing the objects currently selected.
     */
    @property({ type: Array })
    values: string[] = [];

    /**
     * Helper accessor for older code
     */
    get value() {
        return this.values;
    }

    /**
     * One of two criteria (the other being the data-ak-control flag) that specifies this as a
     * control that produces values of specific interest to our REST API. This is our modern
     * accessor name.
     */
    json() {
        return this.values;
    }

    renderHelp() {
        return [
            this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing,
            this.bighelp ? this.bighelp : nothing,
        ];
    }

    handleChange(ev: Event) {
        if (ev.type === "change") {
            this.values = Array.from(this.selectRef.value!.querySelectorAll("option"))
                .filter((option) => option.selected)
                .map((option) => option.value);
            this.dispatchEvent(
                new CustomEvent("ak-select", {
                    detail: this.values,
                    composed: true,
                    bubbles: true,
                }),
            );
        }
    }

    selectRef: Ref<HTMLSelectElement> = createRef();

    render() {
        return html` <div class="pf-c-form">
            <ak-form-element-horizontal
                label=${this.label}
                ?required=${this.required}
                name=${this.name}
            >
                <select
                    part="select"
                    class="pf-c-form-control"
                    name=${ifDefined(this.name)}
                    multiple
                    ${ref(this.selectRef)}
                    @change=${this.handleChange}
                >
                    ${map(
                        this.options,
                        ([value, label]) =>
                            html`<option value=${value} ?selected=${this.values.includes(value)}>
                                ${label}
                            </option>`,
                    )}
                </select>
                ${this.renderHelp()}
            </ak-form-element-horizontal>
        </div>`;
    }
}

export default AkMultiSelect;
