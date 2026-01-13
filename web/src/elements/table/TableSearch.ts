import "#components/ak-search-ql/index";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { PaginatedResponse } from "#elements/table/Table";
import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-table-search")
export class TableSearchForm extends WithLicenseSummary(AKElement) {
    @property({ type: String, reflect: false })
    public defaultValue?: string;

    @property({ type: String })
    public label = msg("Table Search");

    @property({ type: String })
    public placeholder = msg("Search...");

    @property({ attribute: false })
    public supportsQL: boolean = false;

    @property({ attribute: false })
    public apiResponse?: PaginatedResponse<unknown>;

    @property({ attribute: false })
    public onSearch?: (value: string) => void;

    static styles: CSSResult[] = [
        PFBase,
        PFButton,
        PFToolbar,
        PFInputGroup,
        PFFormControl,
        css`
            form.pf-c-input-group {
                position: relative;
            }

            ak-search-ql {
                width: 100%;
            }

            button[type="reset"] {
                position: absolute;
                inset-inline-end: 0.25em;
                inset-block-start: 0.25em;
                appearance: none;
                border: none;
                background: none;
                line-height: 1;
                font-family: ui-monospace, monospace;
                color: initial;
                color: ButtonText;
                z-index: var(--pf-global--ZIndex--xs);
                cursor: pointer;
                display: none;
            }

            ak-search-ql:state(present) + button[type="reset"] {
                display: block;
            }
        `,
    ];

    #formRef = createRef<HTMLFormElement>();

    public reset = (): void => {
        this.#formRef.value?.reset();

        this.onSearch?.("");
    };

    #searchListener = (event: InputEvent) => {
        const target = event.target;

        if (!(target instanceof HTMLInputElement) || !this.onSearch) return;

        // The search event is dispatched by either pressing enter
        // or clearing the input (e.g. via the "x" button or pressing escape).

        // The submit listener handles the enter key, so we only need to handle the clearing here.
        if (target.value) return;

        this.onSearch("");
    };

    #submitListener = (event: SubmitEvent) => {
        event.preventDefault();

        const form = this.#formRef.value;

        if (!form || !this.onSearch) return;

        form.reportValidity();

        const data = new FormData(form);

        const value = data.get("search")?.toString() ?? "";

        this.onSearch(value);
    };

    protected renderInput(): TemplateResult {
        if (this.supportsQL && this.hasEnterpriseLicense) {
            return html`<ak-search-ql
                    label=${ifPresent(this.label)}
                    role="presentation"
                    name="search"
                    placeholder=${ifPresent(this.placeholder)}
                    value=${ifPresent(this.defaultValue)}
                    .apiResponse=${this.apiResponse}
                ></ak-search-ql>
                <button type="reset" aria-label=${msg("Clear search")}>&times;</button>`;
        }

        // The ts-ignore comment is lit-analyzer's solution to "ignore semantic errors in the
        // following HTML code." NOTE: This code needs to be revised. The three common browsers all
        // implement `type="search"` in different and incompatible ways. Safari and Firefox issue
        // `input` events. Firefox treats it as pure `text` field, whereas Safari debounces it
        // according to the `incremental` attribute. Safari's `input` event carries a custom field,
        // `results`, to hint at how many values are currently being found. Consistent behavior will
        // require a custom element that understands the semantics of the delete button and
        // harmonizes the meaning of the `incremental` attribute.
        return html` <!-- @ts-ignore -->
            <input
                aria-label=${ifPresent(this.label)}
                name="search"
                type="search"
                autocomplete="off"
                placeholder=${ifPresent(this.placeholder)}
                value=${ifPresent(this.defaultValue)}
                class="pf-c-form-control"
                @search=${this.#searchListener}
            />`;
    }

    render(): TemplateResult {
        return html`<form
            ${ref(this.#formRef)}
            class="pf-c-input-group"
            @submit=${this.#submitListener}
            @reset=${this.reset}
        >
            ${this.renderInput()}
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-table-search": TableSearchForm;
    }
}
