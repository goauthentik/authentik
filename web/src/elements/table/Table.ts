import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { groupBy } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/chips/Chip";
import "@goauthentik/elements/chips/ChipGroup";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/table/TablePagination";
import "@goauthentik/elements/table/TableSearch";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Pagination, ResponseError } from "@goauthentik/api";

export class TableColumn {
    title: string;
    orderBy?: string;

    onClick?: () => void;

    constructor(title: string, orderBy?: string) {
        this.title = title;
        this.orderBy = orderBy;
    }

    headerClickHandler(table: Table<unknown>): void {
        if (!this.orderBy) {
            return;
        }
        if (table.order === this.orderBy) {
            table.order = `-${this.orderBy}`;
        } else {
            table.order = this.orderBy;
        }
        table.fetch();
    }

    private getSortIndicator(table: Table<unknown>): string {
        switch (table.order) {
            case this.orderBy:
                return "fa-long-arrow-alt-down";
            case `-${this.orderBy}`:
                return "fa-long-arrow-alt-up";
            default:
                return "fa-arrows-alt-v";
        }
    }

    renderSortable(table: Table<unknown>): TemplateResult {
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

    render(table: Table<unknown>): TemplateResult {
        return html`<th
            role="columnheader"
            scope="col"
            class="
                ${this.orderBy ? "pf-c-table__sort " : " "}
                ${table.order === this.orderBy || table.order === `-${this.orderBy}`
                ? "pf-m-selected "
                : ""}
            "
        >
            ${this.orderBy ? this.renderSortable(table) : html`${this.title}`}
        </th>`;
    }
}

export interface PaginatedResponse<T> {
    pagination: Pagination;

    results: Array<T>;
}

export abstract class Table<T> extends AKElement {
    abstract apiEndpoint(page: number): Promise<PaginatedResponse<T>>;
    abstract columns(): TableColumn[];
    abstract row(item: T): TemplateResult[];

    private isLoading = false;

    searchEnabled(): boolean {
        return false;
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    renderExpanded(item: T): TemplateResult {
        if (this.expandable) {
            throw new Error("Expandable is enabled but renderExpanded is not overridden!");
        }
        return html``;
    }

    @property({ attribute: false })
    data?: PaginatedResponse<T>;

    @property({ type: Number })
    page = getURLParam("tablePage", 1);

    @property({ type: String })
    order?: string;

    @property({ type: String })
    search: string = getURLParam("search", "");

    @property({ type: Boolean })
    checkbox = false;

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

    @state()
    hasError?: Error;

    static get styles(): CSSResult[] {
        return [
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
            `,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.fetch();
        });
    }

    public groupBy(items: T[]): [string, T[]][] {
        return groupBy(items, () => {
            return "";
        });
    }

    public async fetch(): Promise<void> {
        if (this.isLoading) {
            return;
        }
        this.isLoading = true;
        try {
            this.data = await this.apiEndpoint(this.page);
            this.hasError = undefined;
            this.page = this.data.pagination.current;
            const newSelected: T[] = [];
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

                const selectedIndex = this.selectedElements.findIndex(comp);
                if (selectedIndex > -1) {
                    newSelected.push(res);
                }
                const expandedIndex = this.expandedElements.findIndex(comp);
                if (expandedIndex > -1) {
                    newExpanded.push(res);
                }
            });
            this.isLoading = false;
            this.selectedElements = newSelected;
            this.expandedElements = newExpanded;
        } catch (ex) {
            this.isLoading = false;
            this.hasError = ex as Error;
        }
    }

    private renderLoading(): TemplateResult {
        return html`<tr role="row">
            <td role="cell" colspan="25">
                <div class="pf-l-bullseye">
                    <ak-empty-state ?loading="${true}" header=${msg("Loading")}> </ak-empty-state>
                </div>
            </td>
        </tr>`;
    }

    renderEmpty(inner?: TemplateResult): TemplateResult {
        return html`<tbody role="rowgroup">
            <tr role="row">
                <td role="cell" colspan="8">
                    <div class="pf-l-bullseye">
                        ${inner
                            ? inner
                            : html`<ak-empty-state
                                  header="${msg("No objects found.")}"
                              ></ak-empty-state>`}
                    </div>
                </td>
            </tr>
        </tbody>`;
    }

    renderError(): TemplateResult {
        return html`<ak-empty-state header="${msg("Failed to fetch objects.")}" icon="fa-times">
            ${this.hasError instanceof ResponseError
                ? html` <div slot="body">${this.hasError.message}</div> `
                : html`<div slot="body">${this.hasError?.toString()}</div>`}
        </ak-empty-state>`;
    }

    private renderRows(): TemplateResult[] | undefined {
        if (this.hasError) {
            return [this.renderEmpty(this.renderError())];
        }
        if (!this.data || this.isLoading) {
            return [this.renderLoading()];
        }
        if (this.data.pagination.count === 0) {
            return [this.renderEmpty()];
        }
        const groupedResults = this.groupBy(this.data.results);
        if (groupedResults.length === 1) {
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
        return items.map((item) => {
            const itemSelectHandler = (ev: InputEvent | PointerEvent) => {
                let checked = false;
                const target = ev.target as HTMLElement;
                if (ev.type === "input") {
                    checked = (target as HTMLInputElement).checked;
                } else if (ev instanceof PointerEvent) {
                    if (target.classList.contains("ignore-click")) {
                        return;
                    }
                    checked = this.selectedElements.indexOf(item) === -1;
                }
                if (checked) {
                    // Prevent double-adding the element to selected items
                    if (this.selectedElements.indexOf(item) !== -1) {
                        return;
                    }
                    // Add item to selected
                    this.selectedElements.push(item);
                } else {
                    // Get index of item and remove if selected
                    const index = this.selectedElements.indexOf(item);
                    if (index <= -1) return;
                    this.selectedElements.splice(index, 1);
                }
                this.requestUpdate();
                // Unset select-all if selectedElements is empty
                const selectAllCheckbox =
                    this.shadowRoot?.querySelector<HTMLInputElement>("[name=select-all]");
                if (!selectAllCheckbox) {
                    return;
                }
                if (this.selectedElements.length < 1) {
                    selectAllCheckbox.checked = false;
                    this.requestUpdate();
                }
            };
            return html`<tbody
                role="rowgroup"
                class="${this.expandedElements.indexOf(item) > -1 ? "pf-m-expanded" : ""}"
            >
                <tr
                    role="row"
                    class="${this.checkbox ? "pf-m-hoverable" : ""}"
                    @click=${itemSelectHandler}
                >
                    ${this.checkbox
                        ? html`<td class="pf-c-table__check" role="cell">
                              <label class="ignore-click"
                                  ><input
                                      type="checkbox"
                                      class="ignore-click"
                                      .checked=${this.selectedElements.indexOf(item) >= 0}
                                      @input=${itemSelectHandler}
                                      @click=${(ev: Event) => {
                                          ev.stopPropagation();
                                      }}
                              /></label>
                          </td>`
                        : html``}
                    ${this.expandable
                        ? html`<td class="pf-c-table__toggle" role="cell">
                              <button
                                  class="pf-c-button pf-m-plain ${this.expandedElements.indexOf(
                                      item,
                                  ) > -1
                                      ? "pf-m-expanded"
                                      : ""}"
                                  @click=${(ev: Event) => {
                                      ev.stopPropagation();
                                      const idx = this.expandedElements.indexOf(item);
                                      if (idx <= -1) {
                                          // Element is not expanded, add it
                                          this.expandedElements.push(item);
                                      } else {
                                          // Element is expanded, remove it
                                          this.expandedElements.splice(idx, 1);
                                      }
                                      this.requestUpdate();
                                  }}
                              >
                                  <div class="pf-c-table__toggle-icon">
                                      &nbsp;<i class="fas fa-angle-down" aria-hidden="true"></i
                                      >&nbsp;
                                  </div>
                              </button>
                          </td>`
                        : html``}
                    ${this.row(item).map((col) => {
                        return html`<td role="cell">${col}</td>`;
                    })}
                </tr>
                <tr
                    class="pf-c-table__expandable-row ${this.expandedElements.indexOf(item) > -1
                        ? "pf-m-expanded"
                        : ""}"
                    role="row"
                >
                    <td></td>
                    ${this.expandedElements.indexOf(item) > -1 ? this.renderExpanded(item) : html``}
                </tr>
            </tbody>`;
        });
    }

    renderToolbar(): TemplateResult {
        return html` <ak-spinner-button
            .callAction=${() => {
                return this.fetch();
            }}
            class="pf-m-secondary"
        >
            ${msg("Refresh")}</ak-spinner-button
        >`;
    }

    renderToolbarSelected(): TemplateResult {
        return html``;
    }

    renderToolbarAfter(): TemplateResult {
        return html``;
    }

    renderSearch(): TemplateResult {
        if (!this.searchEnabled()) {
            return html``;
        }
        return html`<ak-table-search
            class="pf-c-toolbar__item pf-m-search-filter"
            value=${ifDefined(this.search)}
            .onSearch=${(value: string) => {
                this.search = value;
                this.fetch();
                updateURLParams({
                    search: value,
                });
            }}
        >
        </ak-table-search>`;
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    renderSelectedChip(item: T): TemplateResult {
        return html``;
    }

    renderToolbarContainer(): TemplateResult {
        return html`<div class="pf-c-toolbar">
            <div class="pf-c-toolbar__content">
                <div class="pf-c-toolbar__group pf-m-search-filter">${this.renderSearch()}</div>
                <div class="pf-c-toolbar__bulk-select">${this.renderToolbar()}</div>
                <div class="pf-c-toolbar__group">${this.renderToolbarAfter()}</div>
                <div class="pf-c-toolbar__group">${this.renderToolbarSelected()}</div>
                ${this.paginated
                    ? html`<ak-table-pagination
                          class="pf-c-toolbar__item pf-m-pagination"
                          .pages=${this.data?.pagination}
                          .pageChangeHandler=${(page: number) => {
                              this.page = page;
                              updateURLParams({ tablePage: page });
                              this.fetch();
                          }}
                      >
                      </ak-table-pagination>`
                    : html``}
            </div>
        </div>`;
    }

    firstUpdated(): void {
        this.fetch();
    }

    renderTable(): TemplateResult {
        return html` ${this.checkbox && this.checkboxChip
                ? html`<ak-chip-group>
                      ${this.selectedElements.map((el) => {
                          return html`<ak-chip>${this.renderSelectedChip(el)}</ak-chip>`;
                      })}
                  </ak-chip-group>`
                : html``}
            ${this.renderToolbarContainer()}
            <table class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable">
                <thead>
                    <tr role="row">
                        ${this.checkbox
                            ? html`<td class="pf-c-table__check" role="cell">
                                  <input
                                      name="select-all"
                                      type="checkbox"
                                      aria-label=${msg("Select all rows")}
                                      .checked=${this.selectedElements.length ===
                                          this.data?.results.length &&
                                      this.selectedElements.length > 0}
                                      @input=${(ev: InputEvent) => {
                                          if ((ev.target as HTMLInputElement).checked) {
                                              this.selectedElements =
                                                  this.data?.results.slice(0) || [];
                                          } else {
                                              this.selectedElements = [];
                                          }
                                      }}
                                  />
                              </td>`
                            : html``}
                        ${this.expandable ? html`<td role="cell"></td>` : html``}
                        ${this.columns().map((col) => col.render(this))}
                    </tr>
                </thead>
                ${this.renderRows()}
            </table>
            ${this.paginated
                ? html` <div class="pf-c-pagination pf-m-bottom">
                      <ak-table-pagination
                          class="pf-c-toolbar__item pf-m-pagination"
                          .pages=${this.data?.pagination}
                          .pageChangeHandler=${(page: number) => {
                              this.page = page;
                              this.fetch();
                          }}
                      >
                      </ak-table-pagination>
                  </div>`
                : html``}`;
    }

    render(): TemplateResult {
        return this.renderTable();
    }
}
