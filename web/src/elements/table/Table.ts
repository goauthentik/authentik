import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/index";
import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/table/TablePagination";
import "#elements/table/TableSearch";
import "#elements/timestamp/ak-timestamp";

import { BaseTableListRequest, TableLike } from "./shared.js";
import { renderTableColumn, TableColumn } from "./TableColumn.js";

import { EVENT_REFRESH } from "#common/constants";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { GroupResult } from "#common/utils";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithSession } from "#elements/mixins/session";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import Styles from "#elements/table/Table.css";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { isInteractiveElement } from "#elements/utils/interactivity";
import { isEventTargetingListener } from "#elements/utils/pointer";

import { Pagination } from "@goauthentik/api";

import { kebabCase } from "change-case";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { guard } from "lit/directives/guard.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export * from "./shared.js";
export * from "./TableColumn.js";

export interface PaginatedResponse<T> {
    pagination: Pagination;
    autocomplete?: { [key: string]: string };

    results: Array<T>;
}

export function hasPrimaryKey<T extends string | number = string | number>(
    item: object,
): item is { pk: T } {
    return Object.hasOwn(item, "pk");
}

/**
 * An instance of a Table component.
 *
 * This is necessary to work around limitations in Lit's typing system
 * not recognizing abstract properties.
 */
export type TableInstance = InstanceType<typeof Table> & {
    columns: TableColumn[];
};

export abstract class Table<T extends object>
    extends WithLicenseSummary(WithSession(AKElement))
    implements TableLike
{
    static styles: CSSResult[] = [
        PFBase,
        PFTable,
        PFBullseye,
        PFButton,
        PFSwitch,
        PFToolbar,
        PFDropdown,
        PFPagination,
        Styles,
    ];

    protected abstract apiEndpoint(): Promise<PaginatedResponse<T>>;
    /**
     * The columns to display in the table.
     *
     * @abstract
     */
    protected abstract columns: TableColumn[];

    /**
     * Render a row for a given item.
     *
     * @abstract
     */
    protected abstract row(item: T): SlottedTemplateResult[];

    /**
     * The total number of defined and additional columns in the table.
     */
    #columnCount = 0;

    #columnIDs = new WeakMap<TableColumn, string>();

    #synchronizeColumnProperties() {
        let nextColumnCount = this.columns.length;

        if (this.checkbox) nextColumnCount += 1;
        if (this.expandable) nextColumnCount += 1;

        this.#columnCount = nextColumnCount;

        for (const column of this.columns) {
            const [label] = column;

            if (!label) continue;

            const columnName = kebabCase(label);
            this.#columnIDs.set(column, columnName);
        }
    }

    /**
     * Whether the table is currently fetching data.
     */
    @state()
    protected loading = false;

    /**
     * A timestamp of the last attempt to refresh the table data.
     */
    @state()
    protected lastRefreshedAt: Date | null = null;

    /**
     * A cached grouping of the last fetched results.
     *
     * @see {@linkcode Table.fetch}
     */
    @state()
    protected groups: GroupResult<T>[] = [];

    #pageParam = `${this.tagName.toLowerCase()}-page`;
    #searchParam = `${this.tagName.toLowerCase()}-search`;

    @property({ type: Boolean })
    public supportsQL: boolean = false;

    //#region Properties

    @property({ type: String })
    public toolbarLabel: string | null = null;

    @property({ type: String })
    public label: string | null = null;

    @property({ attribute: false })
    public data: PaginatedResponse<T> | null = null;

    @property({ type: Number, useDefault: true })
    public page = getURLParam(this.#pageParam, 1);

    /**
     * Set if your `selectedElements\` use of the selection box is to enable bulk-delete,
     * so that stale data is cleared out when the API returns a new list minus the deleted entries.
     *
     * @prop
     */
    @property({ attribute: "clear-on-refresh", type: Boolean, reflect: true })
    public clearOnRefresh = false;

    @property({ type: String })
    public order?: string;

    @property({ type: String, attribute: false })
    public search?: string;

    @property({ type: Boolean })
    public checkbox = false;

    @property({ type: Boolean })
    public clickable = false;

    @property({ type: Boolean })
    public radioSelect = false;

    @property({ type: Boolean })
    public checkboxChip = false;

    /**
     * A mapping of the current items to their respective identifiers.
     */
    #itemKeys = new WeakMap<T, string | number>();

    /**
     * A mapping of item keys to selected items.
     */
    @property({ attribute: false })
    public selectedMap = new Map<string | number, T>();

    public get selectedElements(): T[] {
        return Array.from(this.selectedMap.values());
    }

    @property({ type: Boolean })
    public paginated = true;

    @property({ type: Boolean })
    public expandable = false;

    @property({ attribute: false })
    public searchLabel?: string;

    @property({ attribute: false })
    public searchPlaceholder?: string;

    //#endregion

    //#region Lifecycle

    @state()
    protected expandedElements = new Set<string | number>();

    @state()
    protected error: APIError | null = null;

    #selectAllCheckboxRef = createRef<HTMLInputElement>();

    #refreshListener = () => {
        return this.fetch();
    };

    public override connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener(EVENT_REFRESH, this.#refreshListener);

        if (this.searchEnabled) {
            this.search = getURLParam(this.#searchParam, "");
        }
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    protected willUpdate(changedProperties: PropertyValues<this>): void {
        const interactive = isInteractiveElement(this);

        if (!interactive) {
            return;
        }

        if (changedProperties.has("page")) {
            updateURLParams({
                [this.#pageParam]: this.page === 1 ? null : this.page,
            });
        }

        if (changedProperties.has("search")) {
            updateURLParams({
                [this.#searchParam]: this.search,
            });
        }
    }

    protected override updated(changedProperties: PropertyValues<this>): void {
        if (
            (changedProperties as PropertyValues<TableInstance>).has("columns") ||
            changedProperties.has("checkbox") ||
            changedProperties.has("expandable")
        ) {
            this.#synchronizeColumnProperties();
        }
    }

    firstUpdated(): void {
        this.fetch();
    }

    //#endregion

    async defaultEndpointConfig(): Promise<BaseTableListRequest> {
        return {
            ordering: this.order,
            page: this.page,
            pageSize: this.uiConfig.pagination.perPage,
            search: this.searchEnabled ? this.search || "" : undefined,
        };
    }

    public fetch(): Promise<void> {
        if (this.loading) {
            return Promise.resolve();
        }

        this.loading = true;

        return this.apiEndpoint()
            .then((data) => {
                this.data = data;
                this.error = null;

                this.groups = this.groupBy(this.data.results);

                this.page = this.data.pagination.current;
                const nextExpanded = new Set<string | number>();

                for (const result of data.results) {
                    const itemKey = hasPrimaryKey(result) ? result.pk : JSON.stringify(result);

                    this.#itemKeys.set(result, itemKey);

                    if (this.expandedElements.has(itemKey)) {
                        nextExpanded.add(itemKey);
                    }
                }

                this.expandedElements = nextExpanded;

                if (this.clearOnRefresh) {
                    if (this.selectedMap.size) {
                        this.selectedMap = new Map();

                        const selectAllCheckbox = this.#selectAllCheckboxRef.value;

                        if (selectAllCheckbox) {
                            selectAllCheckbox.checked = false;
                            selectAllCheckbox.indeterminate = false;
                        }
                    }

                    this.requestUpdate();
                }
            })
            .catch(async (error: unknown) => {
                this.error = await parseAPIResponseError(error);
            })
            .finally(() => {
                this.loading = false;
                this.lastRefreshedAt = new Date();
                this.requestUpdate();
            });
    }

    //#region Render

    protected renderLoading(): TemplateResult {
        return html`<tr role="presentation">
            <td role="presentation" colspan=${this.#columnCount}>
                <div class="pf-l-bullseye">
                    <ak-empty-state default-label></ak-empty-state>
                </div>
            </td>
        </tr>`;
    }

    protected renderEmpty(inner?: SlottedTemplateResult): TemplateResult {
        return html`
            <tr role="presentation">
                <td role="presentation" colspan=${this.#columnCount}>
                    <div class="pf-l-bullseye">
                        ${inner ??
                        html`<ak-empty-state
                            ><span>${msg("No objects found.")}</span>
                            <div slot="primary">${this.renderObjectCreate()}</div>
                        </ak-empty-state>`}
                    </div>
                </td>
            </tr>
        `;
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
            ><span>${msg("Failed to fetch objects.")}</span>
            <div slot="body">${pluckErrorDetail(this.error)}</div>
        </ak-empty-state>`;
    }

    //#region Rows

    /**
     * An overridable event listener when a row is clicked.
     *
     * @bound
     * @abstract
     */
    protected rowClickListener(item: T, event?: InputEvent | PointerEvent): void {
        if (event?.defaultPrevented) {
            return;
        }

        if (isEventTargetingListener(event)) {
            return;
        }

        if (this.expandable) {
            const itemKey = this.#itemKeys.get(item);

            return this.#toggleExpansion(itemKey, event);
        }

        this.#selectItemListener(item, event);
    }

    /**
     * Render a row for a given item.
     *
     * @param item The item to render.
     */
    protected rowLabel(item: T): string | null {
        const name = "name" in item && typeof item.name === "string" ? item.name.trim() : null;

        return name || null;
    }

    private renderRows(): SlottedTemplateResult | SlottedTemplateResult[] {
        if (this.error) {
            return this.renderEmpty(this.renderError());
        }
        if (this.loading && this.data === null) {
            return this.renderLoading();
        }

        if (!this.data?.pagination.count) {
            return this.renderEmpty();
        }

        if (this.groups.length === 1) {
            const [firstGroup] = this.groups;
            const [groupKey, groupItems] = firstGroup;

            if (!groupKey) {
                return html`<tbody>
                    ${groupItems.map((item, itemIndex) =>
                        this.#renderRowGroupItem(item, itemIndex, groupItems, 0),
                    )}
                </tbody>`;
            }
        }

        return this.groups.map(([groupName, items], groupIndex) => {
            const groupHeaderID = `table-group-${groupIndex}`;

            return html`<thead>
                    <tr>
                        <th id=${groupHeaderID} scope="colgroup" colspan=${this.#columnCount}>
                            ${groupName}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map((item, itemIndex) =>
                        this.#renderRowGroupItem(item, itemIndex, items, groupIndex),
                    )}
                </tbody>`;
        });
    }

    //#region Expansion

    protected renderExpanded?(item: T): SlottedTemplateResult;

    #toggleExpansion = (itemKey?: string | number, event?: PointerEvent | InputEvent) => {
        // An unlikely scenario but possible if items shift between fetches
        if (typeof itemKey === "undefined") return;

        event?.stopPropagation();

        const currentTarget = event?.currentTarget as HTMLElement | null;

        if (this.expandedElements.has(itemKey)) {
            this.expandedElements.delete(itemKey);
        } else {
            this.expandedElements.add(itemKey);
            requestAnimationFrame(() => {
                currentTarget?.scrollIntoView({
                    behavior: "smooth",
                });
            });
        }

        // Lit isn't aware of stateful properties,
        // so we need to request an update.
        this.requestUpdate("expandedElements");
    };

    #selectItemListener(item: T, event?: InputEvent | PointerEvent) {
        const { target } = event ?? {};

        const itemKey = this.#itemKeys.get(item);
        const selected = !!(itemKey && this.selectedMap.has(itemKey));
        let checked: boolean;

        if (target instanceof HTMLInputElement) {
            checked = target.checked;
        } else {
            checked = !selected;
        }

        if ((checked && selected) || !(checked || selected)) {
            return;
        }

        event?.stopPropagation();
        event?.preventDefault();

        if (itemKey) {
            if (checked) {
                this.selectedMap.set(itemKey, item);
            } else {
                this.selectedMap.delete(itemKey);
            }

            this.requestUpdate("selectedMap");
        }

        const selectAllCheckbox = this.#selectAllCheckboxRef.value;
        const pageItemCount = this.data?.results?.length ?? 0;
        const selectedCount = this.selectedMap.size;

        if (selectAllCheckbox) {
            selectAllCheckbox.checked = pageItemCount !== 0 && selectedCount !== 0;
            selectAllCheckbox.indeterminate = selectedCount !== 0 && selectedCount < pageItemCount;
        }
    }

    //#region Grouping

    protected groupBy(items: T[]): GroupResult<T>[] {
        return [["", items]];
    }

    #renderRowGroupItem(item: T, rowIndex: number, items: T[], groupIndex: number): TemplateResult {
        const groupHeaderID = this.groups.length > 1 ? `table-group-${groupIndex}` : null;

        const itemKey = this.#itemKeys.get(item);
        const expanded = !!(itemKey && this.expandedElements.has(itemKey));
        const selected = !!(itemKey && this.selectedMap.has(itemKey));

        const memoizedCheckbox = guard([this.checkbox, item, selected], () => {
            if (!this.checkbox) {
                return nothing;
            }

            const rowLabel = this.rowLabel(item) || `#${rowIndex + 1}`;
            const selectItem = this.#selectItemListener.bind(this, item);

            return html`<td class="pf-c-table__check" role="presentation" @click=${selectItem}>
                <label aria-label="${msg(str`Select "${rowLabel}" row`)}"
                    ><input
                        type="checkbox"
                        .checked=${selected}
                        @input=${selectItem}
                        @click=${(event: PointerEvent) => event.stopPropagation()}
                /></label>
            </td>`;
        });

        const memoizedExpansion = guard([this.expandable, itemKey, expanded], () => {
            if (!this.expandable) {
                return nothing;
            }
            const expandItem = this.#toggleExpansion.bind(this, itemKey);

            return html`<td
                class="pf-c-table__toggle pf-m-pressable"
                role="presentation"
                @click=${expandItem}
            >
                <button
                    class="pf-c-button pf-m-plain ${classMap({
                        "pf-m-expanded": expanded,
                    })}"
                    @click=${expandItem}
                    aria-label=${expanded ? msg("Collapse row") : msg("Expand row")}
                    aria-expanded=${expanded.toString()}
                >
                    <div class="pf-c-table__toggle-icon">
                        &nbsp;<i class="fas fa-angle-down" aria-hidden="true"></i>&nbsp;
                    </div>
                </button>
            </td>`;
        });

        let expansionContent: SlottedTemplateResult = nothing;

        if (this.expandable && expanded) {
            if (!this.renderExpanded) {
                throw new TypeError("Expandable is enabled but renderExpanded is not overridden!");
            }

            expansionContent = html`<tr
                class="pf-c-table__expandable-row ${classMap({
                    "pf-m-expanded": expanded,
                })}"
            >
                <td aria-hidden="true"></td>
                <td colspan=${this.#columnCount - 1}>
                    <div class="pf-c-table__expandable-row-content">
                        ${this.renderExpanded(item)}
                    </div>
                </td>
            </tr>`;
        }

        return html`
            <tr
                aria-selected=${selected.toString()}
                class="${classMap({
                    "pf-m-hoverable": this.checkbox || this.expandable || this.clickable,
                })}"
            >
                ${memoizedCheckbox} ${memoizedExpansion}
                ${this.row(item).map((cell, columnIndex) => {
                    const columnID = this.#columnIDs.get(this.columns[columnIndex]);

                    const headers = groupHeaderID
                        ? `${groupHeaderID} ${columnID}`.trim()
                        : columnID;

                    return html`<td
                        @click=${this.rowClickListener.bind(this, item)}
                        class=${ifPresent(!columnID, "presentational")}
                        headers=${ifPresent(headers)}
                    >
                        ${cell}
                    </td>`;
                })}
            </tr>
            ${expansionContent}
        `;
    }

    //#endregion

    //#region Toolbar

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

    protected renderToolbarAfter?(): SlottedTemplateResult;

    protected renderToolbarContainer(): SlottedTemplateResult {
        const label = this.toolbarLabel ?? msg(str`${this.label ?? "Table"} actions`);

        // We need to conditionally render the primary toolbar section
        // to avoid an empty container which applies a gap unnecessarily.
        // This may happen when a table toolbar has an unusual markup,
        // such as in the Recent Events card.

        const primaryToolbar: SlottedTemplateResult[] = [];

        if (this.searchEnabled) {
            primaryToolbar.push(this.renderSearch());
        }

        if (this.renderToolbarAfter) {
            primaryToolbar.push(
                html`<div class="pf-c-toolbar__group" part="toolbar-after">
                    ${this.renderToolbarAfter()}
                </div>`,
            );
        }

        return html`<header
            class="pf-c-toolbar"
            role="toolbar"
            aria-label="${label}"
            part="toolbar"
        >
            ${primaryToolbar.length
                ? html`<div class="pf-c-toolbar__content" part="toolbar-primary">
                      ${primaryToolbar}
                  </div>`
                : nothing}

            <div class="pf-c-toolbar__content" part="toolbar-secondary">
                <div class="pf-c-toolbar__group">
                    ${this.renderToolbar()} ${this.renderToolbarSelected()}
                </div>
                ${this.renderTablePagination()}
            </div>
        </header>`;
    }

    //#endregion

    //#region Search

    #searchListener = (value: string) => {
        this.search = value;
        this.page = 1;
        this.fetch();
    };

    protected searchEnabled = false;

    protected renderSearch(): SlottedTemplateResult {
        if (!this.searchEnabled) {
            return nothing;
        }

        const isQL = this.supportsQL && this.hasEnterpriseLicense;

        return html` <ak-table-search
            class="pf-c-toolbar__item pf-m-search-filter ${isQL ? "ql" : ""}"
            part="toolbar-search"
            .defaultValue=${this.search}
            label=${ifDefined(this.searchLabel)}
            placeholder=${ifDefined(this.searchPlaceholder)}
            .onSearch=${this.#searchListener}
            .supportsQL=${this.supportsQL}
            .apiResponse=${this.data}
        >
        </ak-table-search>`;
    }

    //#endregion

    //#region Chips

    #synchronizeCheckboxAll = () => {
        const checkbox = this.#selectAllCheckboxRef.value;

        if (!checkbox) return;

        checkbox.indeterminate = false;

        const nextSelected = new Map<string | number, T>();

        if (checkbox.checked) {
            const items = this.data?.results || [];

            for (const item of items) {
                const itemKey = this.#itemKeys.get(item);

                if (itemKey) {
                    nextSelected.set(itemKey, item);
                }
            }
        }

        this.selectedMap = nextSelected;
    };

    /**
     * The checkbox on the table header row that allows the user to
     * "activate all on this page,"
     * "deactivate all on this page" with a single click.
     */
    renderAllOnThisPageCheckbox(): TemplateResult {
        const selectedCount = this.selectedMap.size;
        const pageItemCount = this.data?.results?.length ?? 0;

        const checked = pageItemCount !== 0 && selectedCount === pageItemCount;
        const indeterminate =
            pageItemCount !== 0 && selectedCount !== 0 && selectedCount < pageItemCount;

        return html`<th class="pf-c-table__check" role="presentation">
            <input
                ${ref(this.#selectAllCheckboxRef)}
                name="select-all"
                type="checkbox"
                aria-label=${msg(
                    str`Select all rows on page (${selectedCount} of ${pageItemCount} selected)`,
                )}
                .indeterminate=${indeterminate}
                .checked=${checked}
                @input=${this.#synchronizeCheckboxAll}
            />
        </th>`;
    }

    /**
     * For very large tables where the user is selecting a limited number of entries,
     * we provide a chip-based subtable at the top that shows the list of selected entries.
     *
     * Long text result in ellipsized chips, which is sub-optimal.
     */
    protected renderSelectedChip(_item: T): SlottedTemplateResult {
        // Override this for chip-based displays
        return nothing;
    }

    get needChipGroup() {
        return this.checkbox && this.checkboxChip;
    }

    protected renderChipGroup(): TemplateResult {
        return html`<ak-chip-group>
            ${Array.from(this.selectedMap.values(), (item) => {
                return html`<ak-chip>${this.renderSelectedChip(item)}</ak-chip>`;
            })}
        </ak-chip-group>`;
    }

    /**
     * A simple pagination display, shown at both the top and bottom of the page.
     */
    protected renderTablePagination(): SlottedTemplateResult {
        if (!this.paginated) return nothing;

        const handler = (page: number) => {
            this.page = page;
            this.fetch();
        };

        return html`
            <ak-table-pagination
                ?loading=${this.loading}
                label=${ifPresent(this.label)}
                class="pf-c-toolbar__item pf-m-pagination"
                .pages=${this.data?.pagination}
                .onPageChange=${handler}
            >
            </ak-table-pagination>
        `;
    }

    protected renderTable(): TemplateResult {
        const totalItemCount = this.data?.pagination.count ?? -1;

        const renderBottomPagination = () =>
            html`<div class="pf-c-pagination pf-m-bottom">
                <ak-timestamp .timestamp=${this.lastRefreshedAt} refresh>
                    ${msg("Last refreshed")}
                </ak-timestamp>
                ${this.renderTablePagination()}
            </div>`;

        return html`${this.needChipGroup ? this.renderChipGroup() : nothing}
            ${this.renderToolbarContainer()}
            <div part="table-container">
                <table
                    aria-label=${this.label ? msg(str`${this.label} table`) : msg("Table content")}
                    aria-rowcount=${totalItemCount}
                    class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable"
                >
                    <thead aria-label=${msg("Column actions")}>
                        <tr class="pf-c-table__header-row">
                            ${this.checkbox ? this.renderAllOnThisPageCheckbox() : nothing}
                            ${this.expandable ? html`<td aria-hidden="true"></td>` : nothing}
                            ${this.columns.map((column, idx) => {
                                const [label, orderBy, ariaLabel] = column;
                                const columnID = this.#columnIDs.get(column) ?? `column-${idx}`;

                                return renderTableColumn({
                                    label,
                                    id: columnID,
                                    ariaLabel,
                                    orderBy,
                                    table: this,
                                    columnIndex: idx,
                                });
                            })}
                        </tr>
                    </thead>
                    ${this.renderRows()}
                </table>
            </div>
            ${guard([this.paginated, this.lastRefreshedAt], renderBottomPagination)}`;
    }

    render(): TemplateResult {
        return this.renderTable();
    }
}
