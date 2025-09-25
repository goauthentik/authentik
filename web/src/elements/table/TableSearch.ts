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

        return html`<input
            aria-label=${ifPresent(this.label)}
            name="search"
            type="search"
            placeholder=${ifPresent(this.placeholder)}
            value=${ifPresent(this.defaultValue)}
            class="pf-c-form-control"
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
