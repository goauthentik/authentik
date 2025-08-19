import "#components/ak-search-ql/index";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { PaginatedResponse } from "#elements/table/Table";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
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
            ::-webkit-search-cancel-button {
                display: none;
            }
            ak-search-ql {
                width: 100%;
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

    renderInput(): TemplateResult {
        if (this.supportsQL && this.hasEnterpriseLicense) {
            return html`<ak-search-ql
                aria-label=${ifDefined(this.label)}
                name="search"
                required
                placeholder=${ifDefined(this.placeholder)}
                value=${ifDefined(this.defaultValue)}
                .apiResponse=${this.apiResponse}
            ></ak-search-ql>`;
        }

        return html`<input
            aria-label=${ifDefined(this.label)}
            name="search"
            required
            placeholder=${ifDefined(this.placeholder)}
            value=${ifDefined(this.defaultValue)}
            class="pf-c-form-control"
        />`;
    }

    render(): TemplateResult {
        return html`<form
            ${ref(this.#formRef)}
            class="pf-c-input-group"
            @submit=${this.#submitListener}
        >
            ${this.renderInput()}
            <button
                aria-label=${msg("Clear search")}
                class="pf-c-button pf-m-control"
                type="reset"
                @click=${this.reset}
            >
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
            <button aria-label=${msg("Search")} type="submit" class="pf-c-button pf-m-control">
                <i class="fas fa-search" aria-hidden="true"></i>
            </button>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-table-search": TableSearchForm;
    }
}
