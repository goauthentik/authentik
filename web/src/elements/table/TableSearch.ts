import { WithLicenseSummary } from "#elements/mixins/license";
import "@goauthentik/components/ak-search-ql";
import { AKElement } from "@goauthentik/elements/Base";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { LicenseSummaryStatusEnum } from "@goauthentik/api";

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

    static get styles(): CSSResult[] {
        return [
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
    }

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

                const element = this.shadowRoot?.querySelector<
                    HTMLInputElement | HTMLTextAreaElement
                >("[name=search]");

                if (!element?.value) return;

                this.onSearch(element.value);
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
