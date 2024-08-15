import { bound } from "@goauthentik/elements/decorators/bound";
import "@goauthentik/elements/table/standalone/table.js";
import { match } from "ts-pattern";

import { TemplateResult } from "lit";
import { customElement } from "lit/decorators";
import { map } from "lit/directives/map.js";

function toggleSetItem<T>(set: Set<T>, item: T) {
    if (set.has(item)) {
        set.delete(item);
    } else {
        set.add(item);
    }
}

enum SortBy {
    None,
    Up,
    Down,
}

export class SortEvent extends Event {
    static readonly eventName = "sort";
    constructor() {
        super(SortEvent.eventName, { composed: true, bubbles: true });
    }
}

export class TableColumn {
    value: string;
    host!: HTMLElement;
    orderBy?: SortBy;

    constructor(value: string, orderBy?: SortBy, host?: HTMLElement) {
        this.value = value;
        this.orderBy = orderBy;
        if (host) {
            this.host = host;
        }
    }

    private get sortIndicator() {
        return match(this.orderBy)
            .with(SortBy.None, () => "fa-arrows-alt-v")
            .with(SortBy.Up, () => "fa-long-arrow-alt-up")
            .with(SortBy.Down, () => "fa-long-arrow-alt-down")
            .otherwise(() => "");
    }

    private get sortButton() {
        return html` <button class="pf-c-table__button" @click=${() => host.dispatchEvent(new SortEvent())}>
            <div class="pf-c-table__button-content">
                <span class="pf-c-table__text">${this.value}</span>
                <span class="pf-c-table__sort-indicator">
                    <i class="fas ${this.sortIndicator}"></i>
                </span>
            </div>
        </button>`;
    }

    render() {
        const classes = {
            "pf-c-table__sort": !!this.orderBy,
            "pf-m-selected": this.orderBy && this.orderBy !== SortBy.None,
        };

        return html`<th role="columnheader" scope="col" class="${classMap(classes)}">
            ${this.orderBy ? this.sortButton : html`${this.value}`}
        </th>`;
    }
}

function row(binding, label): TemplateResult[] {
    return [
        html`<pre>${binding.order}</pre>`,
        html`${label}`,
        html`<ak-status-label type="warning" ?good=${binding.enabled}></ak-status-label>`,
        html`${binding.timeout}`,
    ];
}

type RowRend = (binding: PolicyBinding) => TemplateResult[];
const policyRow: RowRend = (binding) => row(binding, msg(str`Policy ${binding.policyObj.name}`));
const groupRow: RowRend = (binding) => row(binding, msg(str`Group ${binding.groupObj.name}`));
const userRow: RowRend = (binding) => row(binding, msg(str`User ${binding.userObj.name}`));

type Column = TableColumn | string | [string, string?];

export abstract class Table<T extends object> {
    static get styles() {
        return [PFBase, PFTable];
    }

    abstract get columns(): Column[];
    abstract row(item: T): TemplateResult[];

    private get icolumns(): TableColumn[] {
        const hosted = (column: TableColumn) => {
            column.host = this;
            return host;
        };

        return this.columns.map((column) =>
            typeof column === "string"
                ? hosted(new TableColumn(column))
                : Array.isArray(column)
                  ? new hosted(TableColumn(...column))
                  : hosted(column)
        );
    }

    renderRow(row: T) {
        return html` <tr role="row">
            ${map(this.row(row), (col) => html`<td role="cell">${col}</td>`)}
        </tr>`;
    }

    renderRows(rows: TableRow[]) {
        return html`${map(rows, this.renderRow)}`;
    }

    renderRowGroup(rowGroup: TableGroup) {
        // prettier-ignore
        return html`${map(rowGroup, ({ name, items }) =>
            html` <thead>
                      <tr role="row">
                            <th role="columnheader" scope="row" colspan="200">${name}</th>
                        </tr>
                  </thead>
                  ${this.renderRows(items)}`
            )}`;
    }

    renderGroupedRows(rowGroups: TableGroup[]) {
        return html`${map(rowGroups, this.renderRowGroup)}`;
    }

    public renderRows() {
        // prettier-ignore
        return this.data.grouped
            ? this.renderGroupedResults(this.data.items)
            : this.renderRows(this.data.items);
    }

    public renderTable() {
        return html`
            <table class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable">
                <thead>
                    <tr role="row">
                        ${this.checkbox ? this.renderAllOnThisPageCheckbox() : nothing}
                        ${map(this.icolumns, (col) => col.render(this))}
                    </tr>
                </thead>
                ${this.renderRows()}
            </table>
        `;
    }

    public render() {
        return this.renderTable();
    }
}

export abstract class SelectTable<T extends object> extends Table<T> {
    abstract get key(): string;

    @bound
    onSelectElement(key: string) {
        toggleSetItem(this.selectedElements(key));
    }

    renderCheckbox(item: T) {
        const stop = (ev: Event) => ev.stopPropagation();
        html`<td class="pf-c-table__check" role="cell">
            <label class="ignore-click"
                ><input
                    type="checkbox"
                    class="ignore-click"
                    ?checked=${this.selectedElements.has(this.key(item))}
                    @input=${this.onSelectElement(this.key(item))}
                    @click=${stop}
            /></label>
        </td>`;
    }
}

@customElement("ak-policy-wizard-bound-policies-table")
export class BoundPoliciesTable extends Table<PolicyBinding> {
    checkbox = true;

    columns: TableColumns = [
        [msg("Order"), "order"],
        [msg("Policy / User / Group")],
        [msg("Enabled"), "enabled"],
        [msg("Timeout"), "timeout"],
        [msg("Actions")],
    ];

    row(item: PolicyBinding) {
        const rowRenderer = item.policy ? policyRow : item.user ? userRow : groupRow;
        return rowRenderer(item);
    }
}
