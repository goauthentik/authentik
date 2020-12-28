import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
import { COMMON_STYLES } from "../../common/styles";

@customElement("ak-table-search")
export class TableSearch extends LitElement {

    @property()
    value?: string;

    @property()
    onSearch?: (value: string) => void;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <form class="pf-c-input-group" method="GET" @submit=${(e: Event) => {
        e.preventDefault();
        if (!this.onSearch) return;
        const el = this.shadowRoot?.querySelector<HTMLInputElement>("input[type=search]");
        if (!el) return;
        if (el.value === "") return;
        this.onSearch(el?.value);
    }}>
                        <input class="pf-c-form-control" name="search" type="search" placeholder="Search..." value="${ifDefined(this.value)}" @search=${(ev: Event) => {
    if (!this.onSearch) return;
    this.onSearch((ev.target as HTMLInputElement).value);
}}>
                        <button class="pf-c-button pf-m-control" type="submit">
                            <i class="fas fa-search" aria-hidden="true"></i>
                        </button>
                    </form>
                </div>
            </div>`;
    }

}
