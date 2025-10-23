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
import { uiConfig } from "#common/ui/config";
import { GroupResult } from "#common/utils";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Pagination } from "@goauthentik/api";

import { kebabCase } from "change-case";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref } from "lit/directives/ref.js";
import { repeat } from "lit/directives/repeat.js";

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
    extends WithLicenseSummary(AKElement)
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
        css`
            :host {
                container-type: inline-size;
            }

            [part="table-container"] {
                @media (max-width: 1199px) {
                    overflow-x: auto;
                }
            }

            .pf-c-table {
                .presentational {
                    --pf-c-table--cell--MinWidth: 0;
                }
                @container (width > 1200px) {
                    --pf-c-table--cell--MinWidth: 9em;
                }
            }

            /**
             * TODO: Row actions need a better approach to alignment,
             * but this will at least get the buttons in a grid-like layout.
             */
            td:has(ak-action-button),
            td:has(ak-forms-modal),
            td:has(ak-rbac-object-permission-modal) {
                & > .pf-c-button,
                & > button[slot="trigger"]:has(i),
                & > *::part(spinner-button),
                & > *::part(button) {
                    --pf-global--spacer--form-element: 0;

                    padding-inline: 0.5em !important;
                }

                button[slot="trigger"]:has(i) {
                    padding-inline-start: 0 !important;
                    padding-inline-end: 0.25em !important;
                }

                *::part(spinner-button) {
                    padding-inline-start: 0.5em !important;
                }

                button.pf-m-tertiary {
                    margin-inline-start: 0.25em;
                }

                & > * {
                    display: inline-flex;
                    place-items: center;
                    justify-content: center;
                }
            }

            .pf-m-search-filter {
                flex: 1 1 auto;
                margin-inline: 0;
            }
            .pf-c-table thead .pf-c-table__check {
                min-width: 3rem;
            }
            .pf-c-table tbody .pf-c-table__check input {
                margin-top: calc(var(--pf-c-table__check--input--MarginTop) + 1px);
            }

            .pf-c-toolbar {
                display: flex;
                flex-flow: row wrap;
                padding-inline: var(--pf-global--spacer--md);
                gap: var(--pf-global--spacer--sm);
            }

            .pf-c-toolbar__content {
                flex: 1 1 auto;
                flex-flow: row wrap;
                margin: 0;
                justify-content: space-between;
                gap: var(--pf-global--spacer--sm);
                padding-inline: 0;
                .pf-c-switch {
                    --pf-c-switch--ColumnGap: var(--pf-c-toolbar__item--m-search-filter--spacer);
                }
            }

            .pf-c-toolbar__group {
                flex-flow: row wrap;
                gap: var(--pf-global--spacer--sm);

                .pf-c-card__title .pf-icon {
                    margin-inline-end: var(--pf-global--spacer--sm);
                }
            }

            [part="toolbar-primary"] {
                flex: 2 1 auto;
            }

            .pf-c-table {
                --pf-c-table--m-striped__tr--BackgroundColor: var(
                    --pf-global--BackgroundColor--dark-300
                );
            }

            /**
             * Prevents text selection from interfering with click events
             * when rapidly interacting with cells.
             */
            thead,
            .pf-c-table tr.pf-m-hoverable {
                user-select: none;
            }

            time {
                text-transform: capitalize;
            }

            .pf-c-pagination {
                ak-timestamp {
                    font-size: 0.75rem;
                    font-style: italic;
                    color: var(--pf-global--Color--200);

                    &::part(label) {
                        display: inline-block;
                    }

                    &::part(elapsed) {
                        display: inline-block;
                    }
                }
            }

            /**
             * TODO: Remove after <dialog> modals are implemented.
             */
            .pf-c-dropdown__menu:has(ak-forms-modal) {
                z-index: var(--pf-global--ZIndex--lg);
            }
        `,
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

    @state()
    protected loading = false;

    @state()
    protected lastRefreshedAt: Date | null = null;

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
     * Set if your `selectedElements` use of the selection box is to enable bulk-delete,
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

    #itemKeys = new WeakMap<T, string | number>();

    @property({ attribute: false })
    public get selectedElements(): T[] {
        const items = this.data?.results ?? [];

        return items.filter((item) => {
            const itemKey = this.#itemKeys.get(item);

            if (!itemKey) return false;

            return this.#selectedElements.has(itemKey);
        });
    }

    public set selectedElements(value: Iterable<T>) {
        const nextSelected = new Map<string | number, T>();

        for (const item of value) {
            const itemKey = hasPrimaryKey(item) ? item.pk : JSON.stringify(item);

            this.#itemKeys.set(item, itemKey);

            if (this.#selectedElements.has(itemKey)) {
                nextSelected.set(itemKey, item);
            }
        }

        this.#selectedElements = nextSelected;
    }

    #selectedElements = new Map<string | number, T>();

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
            pageSize: (await uiConfig()).pagination.perPage,
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
                    if (this.#selectedElements.size) {
                        this.#selectedElements.clear();

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

        const groups = this.groupBy(this.data.results);

        if (groups.length === 1) {
            const [firstGroup] = groups;
            const [groupKey, groupItems] = firstGroup;

            if (!groupKey) {
                return html`<tbody>
                    ${repeat(
                        groupItems,
                        (item, itemIndex) => this.#itemKeys.get(item) ?? itemIndex,
                        (item, itemIndex) =>
                            this.#renderRowGroupItem(item, itemIndex, groupItems, 0, groups),
                    )}
                </tbody>`;
            }
        }

        return repeat(
            groups,
            ([group]) => group,
            ([group, items], groupIndex) => {
                const groupHeaderID = `table-group-${groupIndex}`;

                return html`<thead>
                        <tr>
                            <th id=${groupHeaderID} scope="colgroup" colspan=${this.#columnCount}>
                                ${group}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        ${repeat(
                            items,
                            (item, itemIndex) => this.#itemKeys.get(item) ?? itemIndex,
                            (item, itemIndex) =>
                                this.#renderRowGroupItem(
                                    item,
                                    itemIndex,
                                    items,
                                    groupIndex,
                                    groups,
                                ),
                        )}
                    </tbody>`;
            },
        ) as SlottedTemplateResult[];
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
        const { target, currentTarget } = event ?? {};

        const itemKey = this.#itemKeys.get(item);
        const selected = !!(itemKey && this.#selectedElements.has(itemKey));
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
                this.#selectedElements.set(itemKey, item);
            } else {
                this.#selectedElements.delete(itemKey);
            }
        }

        const selectAllCheckbox = this.#selectAllCheckboxRef.value;
        const pageItemCount = this.data?.results?.length ?? 0;
        const selectedCount = this.#selectedElements.size;

        if (selectAllCheckbox) {
            selectAllCheckbox.checked = pageItemCount !== 0 && selectedCount !== 0;
            selectAllCheckbox.indeterminate = selectedCount !== 0 && selectedCount < pageItemCount;
        }

        this.requestUpdate();
    }

    //#region Grouping

    protected groupBy(items: T[]): GroupResult<T>[] {
        return [["", items]];
    }

    #renderRowGroupItem(
        item: T,
        rowIndex: number,
        items: T[],
        groupIndex: number,
        groups: GroupResult<T>[],
    ): TemplateResult {
        const groupHeaderID = groups.length > 1 ? `table-group-${groupIndex}` : null;

        const itemKey = this.#itemKeys.get(item);
        const expanded = !!(itemKey && this.expandedElements.has(itemKey));
        const selected = !!(itemKey && this.#selectedElements.has(itemKey));

        const rowLabel = this.rowLabel(item) || `#${rowIndex + 1}`;
        const rowKey = `row-${groupIndex}-${rowIndex}`;

        const selectItem = this.#selectItemListener.bind(this, item);

        const renderCheckbox = () =>
            html`<td class="pf-c-table__check" role="presentation" @click=${selectItem}>
                <label aria-label="${msg(str`Select "${rowLabel}" row`)}"
                    ><input
                        type="checkbox"
                        .checked=${selected}
                        @input=${selectItem}
                        @click=${(event: PointerEvent) => event.stopPropagation()}
                /></label>
            </td>`;

        const expandItem = this.#toggleExpansion.bind(this, itemKey);

        const renderExpansion = () => {
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
        };

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
                @click=${this.rowClickListener.bind(this, item)}
                aria-selected=${selected.toString()}
                class="${classMap({
                    "pf-m-hoverable": this.checkbox || this.clickable,
                })}"
            >
                ${this.checkbox ? renderCheckbox() : nothing}
                ${this.expandable ? renderExpansion() : nothing}
                ${repeat(
                    this.row(item),
                    (_cell, columnIndex) => columnIndex,
                    (cell, columnIndex) => {
                        const columnID = this.#columnIDs.get(this.columns[columnIndex]);

                        const headers = groupHeaderID
                            ? `${groupHeaderID} ${columnID}`.trim()
                            : columnID;

                        return html`<td
                            class=${ifPresent(!columnID, "presentational")}
                            headers=${ifPresent(headers)}
                        >
                            ${cell}
                        </td>`;
                    },
                )}
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

        if (checkbox.checked) {
            const items = this.data?.results || [];
            const nextSelected = new Map<string | number, T>();

            for (const item of items) {
                const itemKey = this.#itemKeys.get(item);

                if (itemKey) {
                    nextSelected.set(itemKey, item);
                }
            }

            this.#selectedElements = nextSelected;
        } else {
            this.#selectedElements.clear();
        }

        this.requestUpdate();
    };

    /**
     * The checkbox on the table header row that allows the user to
     * "activate all on this page,"
     * "deactivate all on this page" with a single click.
     */
    renderAllOnThisPageCheckbox(): TemplateResult {
        const selectedCount = this.#selectedElements.size;
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
            ${Array.from(this.#selectedElements.values(), (item) => {
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
                            ${repeat(
                                this.columns,
                                ([label], idx) => label ?? idx,
                                (column, idx) => {
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
                                },
                            )}
                        </tr>
                    </thead>
                    ${this.renderRows()}
                </table>
            </div>
            ${this.paginated ? renderBottomPagination() : nothing}`;
    }

    render(): TemplateResult {
        return this.renderTable();
    }
}
