import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-table-search")
export class TableSearch extends AKElement {
    @property()
    public value?: string;

    @property()
    public onSearch?: (value: string) => void;

    @property()
    public label: string = msg("Search");

    @property()
    public placeholder: string = msg("Search…");

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
        `,
    ];

    #resetListener = () => {
        this.onSearch?.("");
    };

    #submitListener = (event: SubmitEvent) => {
        event.preventDefault();
        if (!this.onSearch) return;

        const formData = new FormData(event.target as HTMLFormElement);
        const searchValue = formData.get("search");

        if (typeof searchValue !== "string") return;

        this.onSearch(searchValue);
    };

    render(): TemplateResult {
        return html`<form
            class="pf-c-input-group"
            @submit=${this.#submitListener}
            role="search"
            aria-label="Table search"
        >
            <input
                aria-label="${this.label}"
                class="pf-c-form-control"
                name="search"
                type="search"
                placeholder="${this.placeholder}"
                value="${ifDefined(this.value)}"
            />
            <button
                aria-label=${msg("Reset Search")}
                class="pf-c-button pf-m-control"
                type="reset"
                @click=${this.#resetListener}
            >
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
            <button aria-label=${msg("Search")} class="pf-c-button pf-m-control" type="submit">
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
