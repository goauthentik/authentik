import { EVENT_REFRESH } from "@goauthentik/common/constants";
import {
    APIError,
    parseAPIResponseError,
    pluckErrorDetail,
} from "@goauthentik/common/errors/network";
import { uiConfig } from "@goauthentik/common/ui/config";
import { groupBy } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/chips/Chip";
import "@goauthentik/elements/chips/ChipGroup";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/table/TablePagination";
import { TablePageChangeListener } from "@goauthentik/elements/table/TablePagination";
import "@goauthentik/elements/table/TableSearch";
import { SlottedTemplateResult } from "@goauthentik/elements/types";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Pagination } from "@goauthentik/api";

export interface DefaultAPIEndpointConfig {
    ordering?: string;
    page: number;
    pageSize: number;
    search?: string;
}

export interface TableLike {
    order?: string;
    fetch: () => void;
}

export class TableColumn {
    title: string;
    orderBy?: string;

    onClick?: () => void;

    constructor(title: string, orderBy?: string) {
        this.title = title;
        this.orderBy = orderBy;
    }

    headerClickHandler(table: TableLike): void {
        if (!this.orderBy) {
            return;
        }
        table.order = table.order === this.orderBy ? `-${this.orderBy}` : this.orderBy;
        table.fetch();
    }

    private getSortIndicator(table: TableLike): string {
        switch (table.order) {
            case this.orderBy:
                return "fa-long-arrow-alt-down";
            case `-${this.orderBy}`:
                return "fa-long-arrow-alt-up";
            default:
                return "fa-arrows-alt-v";
        }
    }

    renderSortable(table: TableLike): TemplateResult {
        return html` <button
            class="pf-c-table__button"
            @click=${() => this.headerClickHandler(table)}
        >
            <div class="pf-c-table__button-content">
                <span class="pf-c-table__text">${this.title}</span>
                <span class="pf-c-table__sort-indicator">
                    <i class="fas ${this.getSortIndicator(table)}"></i>
                </span>
            </div>
        </button>`;
    }

    render(table: TableLike): TemplateResult {
        const classes = {
            "pf-c-table__sort": !!this.orderBy,
            "pf-m-selected": table.order === this.orderBy || table.order === `-${this.orderBy}`,
        };

        return html`<th
            aria-label="${this.title}"
            role="columnheader"
            scope="col"
            class="${classMap(classes)}"
        >
            ${this.orderBy ? this.renderSortable(table) : html`${this.title}`}
        </th>`;
    }
}

export interface PaginatedResponse<T> {
    pagination: Pagination;

    results: Array<T>;
}

export abstract class Table<T extends object> extends AKElement implements TableLike {
    /**
     * The API endpoint to fetch data from.
     * @abstract
     */
    protected abstract apiEndpoint(): Promise<PaginatedResponse<T>>;

    /**
     * The columns to display in the table.
     * @abstract
     */
    protected abstract columns(): TableColumn[];

    /**
     * Render a row for a given item.
     *
     * @param item The item to render.
     * @abstract
     */
    protected abstract row(item: T): SlottedTemplateResult[];

    /**
     * Render a row for a given item.
     *
     * @param item The item to render.
     * @abstract
     */
    protected rowLabel(item: T): string | typeof nothing {
        if ("name" in item && typeof item.name === "string") {
            return msg(str`${item.name}`);
        }

        return nothing;
    }

    #loading = false;

    protected searchEnabled(): boolean {
        return false;
    }

    renderExpanded(_item: T): SlottedTemplateResult {
        if (this.expandable) {
            throw new Error("Expandable is enabled but renderExpanded is not overridden!");
        }

        return nothing;
    }

    //#region Properties

    @property({ type: String })
    toolbarLabel = msg("Table actions");

    @property({ type: String })
    label?: string;

    @property({ attribute: false })
    data?: PaginatedResponse<T>;

    @property({ type: Number })
    page = getURLParam("tablePage", 1);

    /**
     * Set if your `selectedElements` use of the selection box is to enable bulk-delete,
     * so that stale data is cleared out when the API returns a new list minus the deleted entries.
     *
     * @prop
     */
    @property({ attribute: "clear-on-refresh", type: Boolean, reflect: true })
    clearOnRefresh = false;

    @property({ type: String })
    order?: string;

    @property({ type: String })
    search: string = "";

    @property({ type: Boolean })
    checkbox = false;

    @property({ type: Boolean })
    clickable = false;

    @property({ attribute: false })
    clickHandler: (item: T) => void = () => {};

    @property({ type: Boolean })
    radioSelect = false;

    @property({ type: Boolean })
    checkboxChip = false;

    @property({ attribute: false })
    selectedElements: T[] = [];

    @property({ type: Boolean })
    paginated = true;

    @property({ type: Boolean })
    expandable = false;

    @property({ attribute: false })
    expandedElements: T[] = [];

    @property({ attribute: false })
    searchLabel?: string;

    @property({ attribute: false })
    searchPlaceholder?: string;

    //#endregion

    @state()
    error?: APIError;

    //#region Static

    static styles: CSSResult[] = [
        PFBase,
        PFTable,
        PFBullseye,
        PFButton,
        PFSwitch,
        PFToolbar,
        PFDropdown,
        PFPagination,
        css`
            .pf-c-table thead .pf-c-table__check {
                min-width: 3rem;
            }
            .pf-c-table tbody .pf-c-table__check input {
                margin-top: calc(var(--pf-c-table__check--input--MarginTop) + 1px);
            }
            .pf-c-toolbar__content {
                row-gap: var(--pf-global--spacer--sm);
            }
            .pf-c-toolbar__item .pf-c-input-group {
                padding: 0 var(--pf-global--spacer--sm);
            }

            .pf-c-table {
                --pf-c-table--m-striped__tr--BackgroundColor: var(
                    --pf-global--BackgroundColor--dark-300
                );
            }
        `,
    ];

    //#endregion

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, async () => {
            await this.fetch();
        });
        if (this.searchEnabled()) {
            this.search = getURLParam("search", "");
        }
    }

    public async defaultEndpointConfig(): Promise<DefaultAPIEndpointConfig> {
        return {
            ordering: this.order,
            page: this.page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.searchEnabled() ? this.search || "" : undefined,
        };
    }

    public groupBy(items: T[]): [SlottedTemplateResult, T[]][] {
        return groupBy(items, () => {
            return "";
        });
    }

    public async fetch(): Promise<void> {
        if (this.#loading) return;

        this.#loading = true;

        return this.apiEndpoint()
            .then((data) => {
                this.data = data;
                this.error = undefined;

                this.page = this.data.pagination.current;
                const newExpanded: T[] = [];

                this.data.results.forEach((res) => {
                    const jsonRes = JSON.stringify(res);
                    // So because we're dealing with complex objects here, we can't use indexOf
                    // since it checks strict equality, and we also can't easily check in findIndex()
                    // Instead we default to comparing the JSON of both objects, which is quite slow
                    // Hence we check if the objects have `pk` attributes set (as most models do)
                    // and compare that instead, which will be much faster.
                    let comp = (item: T) => {
                        return JSON.stringify(item) === jsonRes;
                    };

                    if (Object.hasOwn(res as object, "pk")) {
                        comp = (item: T) => {
                            return (
                                (item as unknown as { pk: string | number }).pk ===
                                (res as unknown as { pk: string | number }).pk
                            );
                        };
                    }

                    const expandedIndex = this.expandedElements.findIndex(comp);

                    if (expandedIndex > -1) {
                        newExpanded.push(res);
                    }
                });

                this.expandedElements = newExpanded;

                // Clear selections after fetch if clearOnRefresh is true
                if (this.clearOnRefresh) {
                    this.selectedElements = [];
                }
            })
            .catch(async (error: unknown) => {
                this.error = await parseAPIResponseError(error);
            })
            .finally(() => {
                this.#loading = false;
                this.requestUpdate();
            });
    }

    private renderLoading(): TemplateResult {
        return html`<tr role="row">
            <td role="cell" colspan="25">
                <div class="pf-l-bullseye">
                    <ak-empty-state loading
                        ><span slot="header">${msg("Loading")}</span></ak-empty-state
                    >
                </div>
            </td>
        </tr>`;
    }

    protected renderEmpty(inner?: SlottedTemplateResult): TemplateResult {
        return html`<tbody role="rowgroup">
            <tr role="row">
                <td role="cell" colspan="8">
                    <div class="pf-l-bullseye">
                        ${inner ??
                        html`<ak-empty-state
                            ><span slot="header">${msg("No objects found.")}</span> >
                            <div slot="primary">${this.renderObjectCreate()}</div>
                        </ak-empty-state>`}
                    </div>
                </td>
            </tr>
        </tbody>`;
    }

    /**
     * Render the create object button.
     *
     * @abstract
     */
    protected renderObjectCreate(): SlottedTemplateResult {
        return nothing;
    }

    /**
     * Render the error state.
     *
     * @abstract
     */
    protected renderError(): SlottedTemplateResult {
        if (!this.error) return nothing;

        return html`<ak-empty-state icon="fa-ban"
            ><span slot="header">${msg("Failed to fetch objects.")}</span>
            <div slot="body">${pluckErrorDetail(this.error)}</div>
        </ak-empty-state>`;
    }

    private renderRows(): TemplateResult[] | undefined {
        if (this.error) {
            return [this.renderEmpty(this.renderError())];
        }
        if (!this.data || this.#loading) {
            return [this.renderLoading()];
        }
        if (this.data.pagination.count === 0) {
            return [this.renderEmpty()];
        }
        const groupedResults = this.groupBy(this.data.results);
        if (groupedResults.length === 1 && groupedResults[0][0] === "") {
            return this.renderRowGroup(groupedResults[0][1]);
        }
        return groupedResults.map(([group, items]) => {
            return html`<thead>
                    <tr role="row">
                        <th role="columnheader" scope="row" colspan="200">${group}</th>
                    </tr>
                </thead>
                ${this.renderRowGroup(items)}`;
        });
    }

    private renderRowGroup(items: T[]): TemplateResult[] {
        const columns = this.columns();

        return items.map((item) => {
            const itemSelectHandler = (ev: InputEvent | PointerEvent) => {
                const target = ev.target as HTMLElement;
                if (ev instanceof PointerEvent && target.classList.contains("ignore-click")) {
                    return;
                }

                const selected = this.selectedElements.includes(item);
                const checked =
                    ev instanceof PointerEvent ? !selected : (target as HTMLInputElement).checked;

                if ((checked && selected) || !(checked || selected)) {
                    return;
                }

                this.selectedElements = this.selectedElements.filter((i) => i !== item);
                if (checked) {
                    this.selectedElements.push(item);
                }

                const selectAllCheckbox =
                    this.shadowRoot?.querySelector<HTMLInputElement>("[name=select-all]");
                if (selectAllCheckbox && this.selectedElements.length < 1) {
                    selectAllCheckbox.checked = false;
                }

                this.requestUpdate();
            };

            const renderCheckbox = () =>
                html`<td aria-label="${msg("Select row")}" class="pf-c-table__check" role="button">
                    <label class="ignore-click"
                        ><input
                            type="checkbox"
                            class="ignore-click"
                            .checked=${this.selectedElements.includes(item)}
                            @input=${itemSelectHandler}
                            @click=${(ev: Event) => {
                                ev.stopPropagation();
                            }}
                    /></label>
                </td>`;

            const handleExpansion = (ev: Event) => {
                ev.stopPropagation();
                const expanded = this.expandedElements.includes(item);
                this.expandedElements = this.expandedElements.filter((i) => i !== item);
                if (!expanded) {
                    this.expandedElements.push(item);
                }
                this.requestUpdate();
            };

            const expandedClass = {
                "pf-m-expanded": this.expandedElements.includes(item),
            };

            const renderExpansion = () => {
                return html`<td class="pf-c-table__toggle" role="cell">
                    <button
                        class="pf-c-button pf-m-plain ${classMap(expandedClass)}"
                        @click=${handleExpansion}
                    >
                        <div class="pf-c-table__toggle-icon">
                            &nbsp;<i class="fas fa-angle-down" aria-hidden="true"></i>&nbsp;
                        </div>
                    </button>
                </td>`;
            };

            return html`<tbody class="${classMap(expandedClass)}">
                <tr
                    aria-label="${this.rowLabel(item)}"
                    class="${this.checkbox || this.clickable ? "pf-m-hoverable" : ""}"
                    @click=${this.clickable
                        ? () => {
                              this.clickHandler(item);
                          }
                        : itemSelectHandler}
                >
                    ${this.checkbox ? renderCheckbox() : nothing}
                    ${this.expandable ? renderExpansion() : nothing}
                    ${this.row(item).map((column, columnIndex) => {
                        const columnLabel = columns[columnIndex]?.title;

                        return html`<td
                            aria-label=${ifDefined(columnLabel)}
                            data-column-index="${columnIndex}"
                            role="cell"
                        >
                            ${column}
                        </td>`;
                    })}
                </tr>
                <tr class="pf-c-table__expandable-row ${classMap(expandedClass)}" role="row">
                    <td></td>
                    ${this.expandedElements.includes(item) ? this.renderExpanded(item) : nothing}
                </tr>
            </tbody>`;
        });
    }

    protected renderToolbar(): TemplateResult {
        return html` ${this.renderObjectCreate()}
            <ak-spinner-button
                .callAction=${() => {
                    return this.fetch();
                }}
                class="pf-m-secondary"
            >
                ${msg("Refresh")}</ak-spinner-button
            >`;
    }

    protected renderToolbarSelected(): SlottedTemplateResult {
        return nothing;
    }

    protected renderToolbarAfter(): SlottedTemplateResult {
        return nothing;
    }

    #searchListener = (value: string) => {
        this.search = value;

        updateURLParams({
            search: value,
        });

        this.fetch();
    };

    protected renderSearch(): SlottedTemplateResult {
        if (!this.searchEnabled()) {
            return nothing;
        }

        return html`<div class="pf-c-toolbar__group pf-m-search-filter">
            <ak-table-search
                class="pf-c-toolbar__item pf-m-search-filter"
                value=${ifDefined(this.search)}
                label=${ifDefined(this.searchLabel)}
                placeholder=${ifDefined(this.searchPlaceholder)}
                .onSearch=${this.#searchListener}
            >
            </ak-table-search>
        </div>`;
    }

    protected renderToolbarContainer(): SlottedTemplateResult {
        return html`<header class="pf-c-toolbar" role="toolbar" aria-label="${this.toolbarLabel}">
            <div role="presentation" class="pf-c-toolbar__content">
                ${this.renderSearch()}
                <div role="presentation" class="pf-c-toolbar__bulk-select">
                    ${this.renderToolbar()}
                </div>
                <div role="presentation" class="pf-c-toolbar__group">
                    ${this.renderToolbarAfter()}
                </div>
                <div role="presentation" class="pf-c-toolbar__group">
                    ${this.renderToolbarSelected()}
                </div>
                ${this.paginated ? this.renderTablePagination() : nothing}
            </div>
        </header>`;
    }

    public firstUpdated(): void {
        this.fetch();
    }

    /* The checkbox on the table header row that allows the user to "activate all on this page,"
     * "deactivate all on this page" with a single click.
     */
    renderAllOnThisPageCheckbox(): TemplateResult {
        const checked =
            this.selectedElements.length === this.data?.results.length &&
            this.selectedElements.length > 0;

        const onInput = (ev: InputEvent) => {
            this.selectedElements = (ev.target as HTMLInputElement).checked
                ? this.data?.results.slice(0) || []
                : [];
        };

        return html`<td class="pf-c-table__check" role="button">
            <input
                name="select-all"
                type="checkbox"
                aria-label=${msg("Select all rows")}
                .checked=${checked}
                @input=${onInput}
            />
        </td>`;
    }

    /* For very large tables where the user is selecting a limited number of entries, we provide a
     * chip-based subtable at the top that shows the list of selected entries. Long text result in
     * ellipsized chips, which is sub-optimal.
     */
    renderSelectedChip(_item: T): SlottedTemplateResult {
        // Override this for chip-based displays
        return nothing;
    }

    get needChipGroup() {
        return this.checkbox && this.checkboxChip;
    }

    renderChipGroup(): TemplateResult {
        return html`<ak-chip-group>
            ${this.selectedElements.map((el) => {
                return html`<ak-chip>${this.renderSelectedChip(el)}</ak-chip>`;
            })}
        </ak-chip-group>`;
    }

    #pageChangeListener: TablePageChangeListener = (page: number) => {
        updateURLParams({ tablePage: page });
        this.page = page;
        this.fetch();
    };

    /**
     * A simple pagination display, shown at both the top and bottom of the page.
     */
    protected renderTablePagination(): SlottedTemplateResult {
        return html`
            <ak-table-pagination
                class="pf-c-toolbar__item pf-m-pagination"
                .pages=${this.data?.pagination}
                .onPageChange=${this.#pageChangeListener}
            >
            </ak-table-pagination>
        `;
    }

    protected renderTable(): TemplateResult {
        const columns = this.columns();

        return html`${this.needChipGroup ? this.renderChipGroup() : nothing}
            ${this.renderToolbarContainer()}
            <table
                aria-labelledby="table-page-main"
                class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable"
            >
                <thead aria-label="${msg("Table columns")}">
                    <tr role="presentation" class="pf-c-table__header-row">
                        ${this.checkbox ? this.renderAllOnThisPageCheckbox() : nothing}
                        ${this.expandable
                            ? html`<td aria-label="${msg("Expand table row")}" role="cell"></td>`
                            : nothing}
                        ${columns.map((col) => col.render(this))}
                    </tr>
                </thead>
                ${this.renderRows()}
            </table>
            ${this.paginated
                ? html`<div class="pf-c-pagination pf-m-bottom">
                      ${this.renderTablePagination()}
                  </div>`
                : nothing}`;
    }

    render(): TemplateResult {
        return this.renderTable();
    }
}
