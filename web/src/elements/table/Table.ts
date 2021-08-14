import { t } from "@lingui/macro";
import { CSSResult, html, LitElement, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";

import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import AKGlobal from "../../authentik.css";

import "./TablePagination";
import "./TableSearch";
import "../EmptyState";
import "../chips/Chip";
import "../chips/ChipGroup";
import { EVENT_REFRESH } from "../../constants";
import { ifDefined } from "lit-html/directives/if-defined";

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

export abstract class Table<T> extends LitElement {
    abstract apiEndpoint(page: number): Promise<AKResponse<T>>;
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
    data?: AKResponse<T>;

    @property({ type: Number })
    page = 1;

    @property({ type: String })
    order?: string;

    @property({ type: String })
    search?: string;

    @property({ type: Boolean })
    checkbox = false;

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

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFTable,
            PFBullseye,
            PFButton,
            PFToolbar,
            PFDropdown,
            PFPagination,
            AKGlobal,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.fetch();
        });
    }

    public fetch(): void {
        if (this.isLoading) {
            return;
        }
        this.isLoading = true;
        this.apiEndpoint(this.page)
            .then((r) => {
                this.data = r;
                this.page = r.pagination.current;
                r.results.forEach((res) => {
                    const selectedIndex = this.selectedElements.indexOf(res);
                    if (selectedIndex <= -1) {
                        this.selectedElements.splice(selectedIndex, 1);
                    }
                    const expandedIndex = this.expandedElements.indexOf(res);
                    if (expandedIndex <= -1) {
                        this.expandedElements.splice(expandedIndex, 1);
                    }
                });
                this.isLoading = false;
            })
            .catch(() => {
                this.isLoading = false;
            });
    }

    private renderLoading(): TemplateResult {
        return html`<tr role="row">
            <td role="cell" colspan="25">
                <div class="pf-l-bullseye">
                    <ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>
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
                                  header="${t`No objects found.`}"
                              ></ak-empty-state>`}
                    </div>
                </td>
            </tr>
        </tbody>`;
    }

    private renderRows(): TemplateResult[] | undefined {
        if (!this.data) {
            return;
        }
        if (this.data.pagination.count === 0) {
            return [this.renderEmpty()];
        }
        return this.data.results.map((item: T) => {
            return html`<tbody
                role="rowgroup"
                class="${this.expandedElements.indexOf(item) > -1 ? "pf-m-expanded" : ""}"
            >
                <tr role="row">
                    ${this.checkbox
                        ? html`<td class="pf-c-table__check" role="cell">
                              <input
                                  type="checkbox"
                                  .checked=${this.selectedElements.indexOf(item) >= 0}
                                  @input=${(ev: InputEvent) => {
                                      if ((ev.target as HTMLInputElement).checked) {
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
                                      if (this.selectedElements.length < 1) {
                                          const selectAllCheckbox =
                                              this.shadowRoot?.querySelector<HTMLInputElement>(
                                                  "[name=select-all]",
                                              );
                                          if (!selectAllCheckbox) {
                                              return;
                                          }
                                          selectAllCheckbox.checked = false;
                                          this.requestUpdate();
                                      }
                                  }}
                              />
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
                                  @click=${() => {
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
        return html`<button
            @click=${() => {
                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
            }}
            class="pf-c-button pf-m-secondary"
        >
            ${t`Refresh`}
        </button>`;
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
            value=${ifDefined(this.search)}
            .onSearch=${(value: string) => {
                this.search = value;
                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
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
                <div class="pf-m-search-filter">${this.renderSearch()}</div>
                <div class="pf-c-toolbar__bulk-select">${this.renderToolbar()}</div>
                <div class="pf-c-toolbar__group">${this.renderToolbarAfter()}</div>
                <div class="pf-c-toolbar__group">${this.renderToolbarSelected()}</div>
                ${this.paginated
                    ? html`<ak-table-pagination
                          class="pf-c-toolbar__item pf-m-pagination"
                          .pages=${this.data?.pagination}
                          .pageChangeHandler=${(page: number) => {
                              this.page = page;
                              this.dispatchEvent(
                                  new CustomEvent(EVENT_REFRESH, {
                                      bubbles: true,
                                      composed: true,
                                  }),
                              );
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
                                      aria-label=${t`Select all rows`}
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
                ${this.isLoading || !this.data ? this.renderLoading() : this.renderRows()}
            </table>
            ${this.paginated
                ? html` <div class="pf-c-pagination pf-m-bottom">
                      <ak-table-pagination
                          class="pf-c-toolbar__item pf-m-pagination"
                          .pages=${this.data?.pagination}
                          .pageChangeHandler=${(page: number) => {
                              this.page = page;
                              this.dispatchEvent(
                                  new CustomEvent(EVENT_REFRESH, {
                                      bubbles: true,
                                      composed: true,
                                  }),
                              );
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
