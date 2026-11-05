import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";

import { AKElement } from "#elements/Base";
import type { PaginatedResponse } from "#elements/table/Table";
import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import { until } from "lit/directives/until.js";

@customElement("ak-table-search")
export class TableSearchForm extends AKElement {
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
    #searchQLImport: Promise<unknown> | null = null;

    public reset = (): void => {
        this.#formRef.value?.reset();

        this.onSearch?.("");
    };

    #importSearchQL(): Promise<unknown> {
        this.#searchQLImport ??= import("#components/ak-search-ql/index");

        return this.#searchQLImport;
    }

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
        event.stopPropagation();

        const form = this.#formRef.value;

        if (!form || !this.onSearch) return;

        form.reportValidity();

        const data = new FormData(form);

        const value = data.get("search")?.toString() ?? "";

        this.onSearch(value);
    };

    protected renderInput() {
        if (this.supportsQL) {
            const content = this.#importSearchQL().then(
                () => html`<ak-search-ql
                        label=${ifPresent(this.label)}
                        role="presentation"
                        name="search"
                        placeholder=${ifPresent(this.placeholder)}
                        value=${ifPresent(this.defaultValue)}
                        .apiResponse=${this.apiResponse}
                    ></ak-search-ql>
                    <button type="reset" aria-label=${msg("Clear search")}>&times;</button>`,
            );

            return until(content, nothing);
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
                part="search-input"
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
            part="search-form"
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
