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
    value?: string;

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
                .pf-c-form-control {
                    font-family: monospace;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<form
            class="pf-c-input-group"
            method="GET"
            @submit=${(e: Event) => {
                e.preventDefault();
                if (!this.onSearch) return;
                const el = this.shadowRoot?.querySelector<HTMLInputElement>("[name=search]");
                if (!el) return;
                if (el.value === "") return;
                this.onSearch(el?.value);
            }}
        >
            <textarea
                class="pf-c-form-control"
                name="search"
                placeholder=${msg("Search...")}
                spellcheck="false"
                @submit=${(ev: Event) => {
                    if (!this.onSearch) return;
                    this.onSearch((ev.target as HTMLInputElement).value);
                }}
            >${ifDefined(this.value)}</textarea>
            <button
                class="pf-c-button pf-m-control"
                type="reset"
                @click=${() => {
                    if (!this.onSearch) return;
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
