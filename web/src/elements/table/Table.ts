import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/index";
import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/table/TablePagination";
import "#elements/table/TableSearch";

import { TableLike } from "./shared.js";
import { TableColumn } from "./TableColumn.js";

import { EVENT_REFRESH } from "#common/constants";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { uiConfig } from "#common/ui/config";
import { GroupResult } from "#common/utils";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { SlottedTemplateResult } from "#elements/types";

import { Pagination } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
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
            .pf-c-toolbar__group.pf-m-search-filter.ql {
                flex-grow: 1;
            }
            ak-table-search.ql {
                width: 100% !important;
            }
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

            /**
             * Prevents text selection from interfering with click events
             * when rapidly interacting with cells.
             */
            thead,
            .pf-c-table tr.pf-m-hoverable {
                user-select: none;
            }
        `,
    ];

    protected abstract apiEndpoint(): Promise<PaginatedResponse<T>>;
    protected abstract columns(): TableColumn[];
    protected abstract row(item: T): SlottedTemplateResult[];

    #loading = false;

    #pageParam = `${this.tagName.toLowerCase()}-page`;
    #searchParam = `${this.tagName.toLowerCase()}-search`;

    @property({ type: Boolean })
    public supportsQL: boolean = false;

    //#region Properties

    @property({ type: String })
    public toolbarLabel = msg("Table actions");

    @property({ type: String })
    public label?: string;

    @property({ attribute: false })
    public data?: PaginatedResponse<T>;

    @property({ type: Number })
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

    @property({ attribute: false })
    public clickHandler: (item: T) => void = () => {};

    @property({ type: Boolean })
    public radioSelect = false;

    @property({ type: Boolean })
    public checkboxChip = false;

    @property({ attribute: false })
    public selectedElements: Set<T> = new Set();

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

        if (this.searchEnabled()) {
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
                [this.#pageParam]: this.page,
            });
        }
        if (changedProperties.has("search")) {
            updateURLParams({
                [this.#searchParam]: this.search,
            });
        }
    }

    firstUpdated(): void {
        this.fetch();
    }

    //#endregion

    async defaultEndpointConfig() {
        return {
            ordering: this.order,
            page: this.page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.searchEnabled() ? this.search || "" : undefined,
        };
    }

    public fetch(): Promise<void> {
        if (this.#loading) {
            return Promise.resolve();
        }

        this.#loading = true;

        return this.apiEndpoint()
            .then((data) => {
                this.data = data;
                this.error = null;

                this.page = this.data.pagination.current;
                const nextExpanded = new Set<string | number>();

                for (const result of data.results) {
                    const expansionKey = hasPrimaryKey(result) ? result.pk : JSON.stringify(result);

                    if (this.expandedElements.has(expansionKey)) {
                        nextExpanded.add(expansionKey);
                    }
                }

                this.expandedElements = nextExpanded;

                if (this.clearOnRefresh) {
                    this.selectedElements = new Set();
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

    //#region Render

    protected renderLoading(): TemplateResult {
        return html`<tr role="presentation">
            <td role="presentation" colspan="25">
                <div class="pf-l-bullseye">
                    <ak-empty-state default-label></ak-empty-state>
                </div>
            </td>
        </tr>`;
    }

    protected renderEmpty(inner?: SlottedTemplateResult): TemplateResult {
        return html`
            <tr role="presentation">
                <td role="presentation" colspan="8">
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
     * Render a row for a given item.
     *
     * @param item The item to render.
     */
    protected rowLabel<T extends object>(item: T): string | typeof nothing {
        const name = "name" in item && typeof item.name === "string" ? item.name.trim() : null;

        if (!name) {
            return nothing;
        }

        return msg(str`${name}`);
    }

    private renderRows(): SlottedTemplateResult | SlottedTemplateResult[] {
        if (this.error) {
            return this.renderEmpty(this.renderError());
        }

        if (!this.data || this.#loading) {
            return this.renderLoading();
        }

        if (this.data.pagination.count === 0) {
            return this.renderEmpty();
        }

        const groups = this.groupBy(this.data.results);

        if (groups.length === 1) {
            const [firstGroup] = groups;
            const [groupKey, groupItems] = firstGroup;

            if (!groupKey) {
                return html`<tbody>
                    ${groupItems.map((item, itemIndex) =>
                        this.#renderRowGroupItem(item, itemIndex, groupItems, 0, groups),
                    )}
                </tbody>`;
            }
        }

        const columnCount = this.columns().length + (this.checkbox ? 1 : 0);

        return groups.map(([group, items], groupIndex) => {
            const groupHeaderID = `table-group-${groupIndex}`;

            return html`<thead role="presentation">
                    <tr>
                        <th
                            id=${groupHeaderID}
                            role="columnheader"
                            scope="colgroup"
                            colspan=${columnCount}
                        >
                            ${group}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map((item, itemIndex) =>
                        this.#renderRowGroupItem(item, itemIndex, items, groupIndex, groups),
                    )}
                </tbody>`;
        });
    }

    //#region Grouping

    protected groupBy(items: T[]): GroupResult<T>[] {
        return [["", items]];
    }

    protected renderExpanded(_item: T): SlottedTemplateResult {
        if (this.expandable) {
            throw new TypeError("Expandable is enabled but renderExpanded is not overridden!");
        }

        return nothing;
    }

    #toggleExpansion = (expansionKey: string | number, event?: PointerEvent) => {
        event?.stopPropagation();

        const currentTarget = event?.currentTarget as HTMLElement | null;

        if (this.expandedElements.has(expansionKey)) {
            this.expandedElements.delete(expansionKey);
        } else {
            this.expandedElements.add(expansionKey);
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

    #selectItemListener(item: T, event: InputEvent | PointerEvent) {
        const target = event.target as HTMLElement;

        if (event instanceof PointerEvent && target.classList.contains("ignore-click")) {
            return;
        }

        const selected = this.selectedElements.has(item);
        let checked: boolean;

        if (target instanceof HTMLInputElement) {
            checked = target.checked;
        } else {
            checked = !selected;
        }

        if ((checked && selected) || !(checked || selected)) {
            return;
        }

        this.selectedElements.delete(item);

        if (checked) {
            this.selectedElements.add(item);
        }

        const selectAllCheckbox = this.#selectAllCheckboxRef.value;
        const currentItems = this.data?.results || [];

        if (selectAllCheckbox) {
            selectAllCheckbox.checked = !!this.selectedElements.size;
            selectAllCheckbox.indeterminate =
                currentItems.length > 0 && this.selectedElements.size < currentItems.length;
        }

        this.requestUpdate();
    }

    #renderRowGroupItem(
        item: T,
        itemIndex: number,
        items: T[],
        groupIndex: number,
        groups: GroupResult<T>[],
    ): TemplateResult {
        const groupHeaderID = groups.length > 1 ? `table-group-${groupIndex}` : null;

        const expansionKey = hasPrimaryKey(item) ? item.pk : JSON.stringify(item);
        const expanded = this.expandedElements.has(expansionKey);
        const selected = this.selectedElements.has(item);
        const rowLabel = this.rowLabel(item);

        const renderCheckbox = () =>
            html`<td class="pf-c-table__check" role="presentation">
                <label aria-label="${msg(str`Select "${rowLabel}" row`)}" class="ignore-click"
                    ><input
                        type="checkbox"
                        class="ignore-click"
                        .checked=${selected}
                        @input=${this.#selectItemListener.bind(this, item)}
                        @click=${(ev: PointerEvent) => {
                            ev.stopPropagation();
                        }}
                /></label>
            </td>`;

        const renderExpansion = () => {
            return html`<td
                class="pf-c-table__toggle pf-m-pressable"
                role="presentation"
                @click=${this.#toggleExpansion.bind(this, expansionKey)}
            >
                <button
                    class="pf-c-button pf-m-plain ${classMap({
                        "pf-m-expanded": expanded,
                    })}"
                    @click=${this.#toggleExpansion.bind(this, expansionKey)}
                    aria-label=${expanded ? msg("Collapse row") : msg("Expand row")}
                    aria-expanded=${expanded ? "true" : "false"}
                >
                    <div class="pf-c-table__toggle-icon">
                        &nbsp;<i class="fas fa-angle-down" aria-hidden="true"></i>&nbsp;
                    </div>
                </button>
            </td>`;
        };

        return html`
            <tr
                aria-label=${rowLabel}
                aria-selected=${selected ? "true" : "false"}
                class="${classMap({
                    "pf-m-hoverable": this.checkbox || this.clickable,
                })}"
                @click=${this.clickable
                    ? this.clickHandler.bind(this, item)
                    : this.#selectItemListener.bind(this, item)}
            >
                ${this.checkbox ? renderCheckbox() : nothing}
                ${this.expandable ? renderExpansion() : nothing}
                ${this.row(item).map((column, columnIndex) => {
                    const columnHeaderID = `table-header-${columnIndex}`;
                    const headers = groupHeaderID
                        ? `${groupHeaderID} ${columnHeaderID}`
                        : columnHeaderID;

                    return html`<td headers=${headers} role="cell">${column}</td>`;
                })}
            </tr>
            <tr
                class="pf-c-table__expandable-row ${classMap({
                    "pf-m-expanded": expanded,
                })}"
                role="row"
            >
                <td></td>
                ${expanded ? this.renderExpanded(item) : nothing}
            </tr>
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

    protected renderToolbarAfter(): SlottedTemplateResult {
        return nothing;
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

    //#endregion

    //#region Search

    #searchListener = (value: string) => {
        this.search = value;
        this.page = 1;
        this.fetch();
    };

    protected searchEnabled(): boolean {
        return false;
    }

    protected renderSearch(): SlottedTemplateResult {
        if (!this.searchEnabled()) {
            return nothing;
        }

        const isQL = this.supportsQL && this.hasEnterpriseLicense;

        return html`<div class="pf-c-toolbar__group pf-m-search-filter ${isQL ? "ql" : ""}">
            <ak-table-search
                class="pf-c-toolbar__item pf-m-search-filter ${isQL ? "ql" : ""}"
                .defaultValue=${this.search}
                label=${ifDefined(this.searchLabel)}
                placeholder=${ifDefined(this.searchPlaceholder)}
                .onSearch=${this.#searchListener}
                .supportsQL=${this.supportsQL}
                .apiResponse=${this.data}
            >
            </ak-table-search>
        </div>`;
    }

    //#endregion

    //#region Chips

    #synchronizeCheckboxAll = () => {
        const checkbox = this.#selectAllCheckboxRef.value;

        if (!checkbox) return;

        checkbox.indeterminate = false;

        if (checkbox.checked) {
            const items = this.data?.results || [];
            this.selectedElements = new Set(items);
        } else {
            this.selectedElements = new Set();
        }
    };

    /**
     * The checkbox on the table header row that allows the user to
     * "activate all on this page,"
     * "deactivate all on this page" with a single click.
     */
    renderAllOnThisPageCheckbox(): TemplateResult {
        const itemsCount = this.data?.results?.length ?? -1;
        const checked = itemsCount !== -1 && this.selectedElements.size === itemsCount;

        return html`<td class="pf-c-table__check" role="cell">
            <input
                ${ref(this.#selectAllCheckboxRef)}
                name="select-all"
                type="checkbox"
                aria-label=${msg("Select all rows")}
                .checked=${checked}
                @input=${this.#synchronizeCheckboxAll}
            />
        </td>`;
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
            ${Array.from(this.selectedElements, (el) => {
                return html`<ak-chip>${this.renderSelectedChip(el)}</ak-chip>`;
            })}
        </ak-chip-group>`;
    }

    /**
     * A simple pagination display, shown at both the top and bottom of the page.
     */
    protected renderTablePagination(): SlottedTemplateResult {
        const handler = (page: number) => {
            this.page = page;
            this.fetch();
        };

        return html`
            <ak-table-pagination
                class="pf-c-toolbar__item pf-m-pagination"
                .pages=${this.data?.pagination}
                .onPageChange=${handler}
            >
            </ak-table-pagination>
        `;
    }

    protected renderTable(): TemplateResult {
        const renderBottomPagination = () =>
            html`<div class="pf-c-pagination pf-m-bottom">${this.renderTablePagination()}</div>`;

        return html`${this.needChipGroup ? this.renderChipGroup() : nothing}
            ${this.renderToolbarContainer()}
            <table
                aria-label=${this.label ? msg(str`Table of ${this.label}`) : msg("Table content")}
                class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable"
            >
                <thead aria-label=${msg("Column actions")}>
                    <tr role="presentation" class="pf-c-table__header-row">
                        ${this.checkbox ? this.renderAllOnThisPageCheckbox() : nothing}
                        ${this.expandable ? html`<td role="cell"></td>` : nothing}
                        ${this.columns().map((col, idx) => col.render(this, idx))}
                    </tr>
                </thead>
                ${this.renderRows()}
            </table>
            ${this.paginated ? renderBottomPagination() : nothing}`;
    }

    render(): TemplateResult {
        return this.renderTable();
    }
}
