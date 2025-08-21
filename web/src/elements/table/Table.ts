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
import { groupBy } from "#common/utils";

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
        `,
    ];

    abstract apiEndpoint(): Promise<PaginatedResponse<T>>;
    abstract columns(): TableColumn[];
    abstract row(item: T): SlottedTemplateResult[];

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
    public selectedElements: T[] = [];

    @property({ type: Boolean })
    public paginated = true;

    @property({ type: Boolean })
    public expandable = false;

    @property({ attribute: false })
    public expandedElements: T[] = [];

    @property({ attribute: false })
    public searchLabel?: string;

    @property({ attribute: false })
    public searchPlaceholder?: string;

    //#endregion

    //#region Lifecycle

    @state()
    protected error?: APIError;

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

    //#region Render

    protected renderLoading(): TemplateResult {
        return html`<tr role="row">
            <td role="cell" colspan="25">
                <div class="pf-l-bullseye">
                    <ak-empty-state default-label></ak-empty-state>
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
                            ><span>${msg("No objects found.")}</span>
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

    //#region Grouping

    public groupBy(items: T[]): [SlottedTemplateResult, T[]][] {
        return groupBy(items, () => "");
    }

    renderExpanded(_item: T): SlottedTemplateResult {
        if (this.expandable) {
            throw new Error("Expandable is enabled but renderExpanded is not overridden!");
        }

        return nothing;
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

    /**
     * The checkbox on the table header row that allows the user to
     * "activate all on this page,"
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
            ${this.selectedElements.map((el) => {
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
                <thead aria-label=${msg("Table actions")}>
                    <tr role="presentation" class="pf-c-table__header-row">
                        ${this.checkbox ? this.renderAllOnThisPageCheckbox() : nothing}
                        ${this.expandable ? html`<td role="cell"></td>` : nothing}
                        ${this.columns().map((col) => col.render(this))}
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
