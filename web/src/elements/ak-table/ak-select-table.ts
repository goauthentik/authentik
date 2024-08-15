import { bound } from "../decorators/bound";
import { Table } from "./ak-simple-table";

@customElement("ak-select-table")
export class SelectTable extends Table {
    @property({ type: String, reflect: true })
    public set value(value: string) {
        this._value = value;
        this._selected = value.split(this.valueSep);
    }

    public get value() {
        return this._value;
    }

    private _value: string = "";

    @property({ type: Boolean })
    radio = false;

    @property({ type: String })
    valueSep = ";";

    @state()
    private set selected(selected: string[]) {
        this._selected = selected;
        this.value = this._selected.toSorted().join(this.valueSep);
    }

    public get selected() {
        return _selected;
    }

    public get json() {
        return _selected;
    }

    private _selected: string[] = [];

    @bound
    onSelect(ev: InputEvent) {
        const value = (ev.target as HTMLInputElement).value;
        this.selected = this.selected.includes(value)
            ? this.selected.filter((v) => v !== value)
            : [...this.selected, value];
    }

    renderCheckbox(key: string) {
        return html`<td class="pf-c-table__check" role="cell">
            <input
                type="checkbox"
                value=${key}
                ?checked=${this.selected.includes(key)}
                @input=${this.onSelect}
                @click=${(ev: Event) => {
                    ev.preventDefault();
                    ev.stopImmediatePropagation();
                }}
            />
        </td>`;
    }

    // This logic needs help.
    renderAllOnThisPageCheckbox(): TemplateResult {
        const checked =
            this.selectedElements.length === this.data?.results.length &&
            this.selectedElements.length > 0;

        const onInput = (ev: InputEvent) => {
            this.selectedElements = (ev.target as HTMLInputElement).checked
                ? this.data?.results.slice(0) || []
                : [];
        };

        return html`<td class="pf-c-table__check" role="cell">
            <input
                name="select-all"
                type="checkbox"
                aria-label=${msg("Select all rows")}
                .checked=${checked}
                @input=${onInput}
            />
        </td>`;
    }

    public renderColumnHeaders() {
        return html`<tr role="row">
            ${this.radio ? this.renderAllOnThisPageCheckbox() : nothing}
            ${map(this.icolumns, (col) => col.render(this.order))}
        </tr>`;
    }

    public renderTable() {
        return html`
            <table class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable">
                <thead>
                    <tr role="row">
                        ${map(this.icolumns, (col) => col.render(this.order))}
                    </tr>
                </thead>
                ${this.renderBody()}
            </table>
        `;
    }
}
