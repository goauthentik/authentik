import "#components/ak-search-ql/index";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { PaginatedResponse } from "#elements/table/Table";

import { LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-table-search")
export class TableSearch extends WithLicenseSummary(AKElement) {
    @property()
    value?: string;

    @property({ type: Boolean })
    supportsQL: boolean = false;

    @property({ attribute: false })
    apiResponse?: PaginatedResponse<unknown>;

    @property()
    onSearch?: (value: string) => void;

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

    renderInput(): TemplateResult {
        if (
            this.supportsQL &&
            this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed
        ) {
            return html`<ak-search-ql
                .apiResponse=${this.apiResponse}
                .value=${this.value}
                .onSearch=${(value: string) => {
                    if (!this.onSearch) return;
                    this.onSearch(value);
                }}
                name="search"
            ></ak-search-ql>`;
        }
        return html`<input
            class="pf-c-form-control"
            name="search"
            type="search"
            placeholder=${msg("Search...")}
            value="${ifDefined(this.value)}"
            @search=${(ev: Event) => {
                if (!this.onSearch) return;
                this.onSearch((ev.target as HTMLInputElement).value);
            }}
        />`;
    }

    render(): TemplateResult {
        return html`<form
            class="pf-c-input-group"
            method="get"
            @submit=${(event: SubmitEvent) => {
                event.preventDefault();

                if (!this.onSearch) return;

                const el = this.shadowRoot?.querySelector<HTMLInputElement | HTMLTextAreaElement>(
                    "[name=search]",
                );

                if (!el) return;
                if (el.value === "") return;

                this.onSearch(el?.value);
            }}
        >
            ${this.renderInput()}
            <button
                class="pf-c-button pf-m-control"
                type="reset"
                @click=${() => {
                    if (!this.onSearch) return;
                    this.value = "";
                    this.onSearch("");
                }}
            >
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
            <button class="pf-c-button pf-m-control" type="submit">
                <i class="fas fa-search" aria-hidden="true"></i>
            </button>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-table-search": TableSearch;
    }
}
