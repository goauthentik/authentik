import "#elements/EmptyState";

import { updateURLParams } from "#elements/router/RouteMatch";
import { Table } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFSidebar from "@patternfly/patternfly/components/Sidebar/sidebar.css";

export abstract class TablePage<T extends object> extends Table<T> {
    static styles: CSSResult[] = [
        // ---
        ...super.styles,
        PFPage,
        PFContent,
        PFSidebar,
        css`
            :host {
                display: flex;
            }

            .pf-c-sidebar__panel {
                --pf-c-sidebar__panel--Position: static;
                flex: 0 1 25%;
            }
            .pf-c-sidebar__content {
                flex: 1 1 75%;
            }
        `,
    ];

    //#region Abstract properties

    /**
     * The title of the page.
     * @abstract
     */
    public abstract pageTitle: string;

    /**
     * The description of the page.
     * @abstract
     */
    public abstract pageDescription: string;

    /**
     * The icon to display in the page header.
     * @abstract
     */
    public abstract pageIcon: string;

    //#endregion

    //#region Lifecycle

    public override connectedCallback(): void {
        super.connectedCallback();

        this.label ??= this.pageTitle;
    }

    //#endregion

    //#region Abstract methods

    /**
     * Render content before the sidebar.
     * @abstract
     */
    protected renderSidebarBefore?(): TemplateResult;

    /**
     * Render content after the sidebar.
     * @abstract
     */
    protected renderSidebarAfter?(): TemplateResult;

    /**
     * Render content before the main section.
     * @abstract
     */
    protected renderSectionBefore?(): TemplateResult;

    /**
     * Render content after the main section.
     * @abstract
     */
    protected renderSectionAfter?(): TemplateResult;

    //#endregion

    //#region Protected methods

    protected clearSearch = () => {
        this.search = "";

        this.requestUpdate();

        updateURLParams({
            search: "",
        });

        return this.fetch();
    };

    //#endregion

    //#region Render methods

    /**
     * Render the empty state.
     */
    protected renderEmpty(inner?: TemplateResult): TemplateResult {
        return super.renderEmpty(html`
            ${inner
                ? inner
                : html`<ak-empty-state icon=${this.pageIcon}
                      ><span>${this.emptyStateMessage}</span>
                      <div slot="body">
                          ${this.searchEnabled ? this.renderEmptyClearSearch() : nothing}
                      </div>
                      <div slot="primary">${this.renderObjectCreate()}</div>
                  </ak-empty-state>`}
        `);
    }

    protected renderEmptyClearSearch(): SlottedTemplateResult {
        if (!this.search) {
            return nothing;
        }
        return html`<button
            @click=${() => {
                this.search = "";
                this.requestUpdate();
                this.fetch();
                this.page = 1;
            }}
            class="pf-c-button pf-m-link"
        >
            ${msg("Clear search")}
        </button>`;
    }

    render() {
        return html` ${this.renderSectionBefore?.()}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-c-sidebar pf-m-gutter">
                    <div class="pf-c-sidebar__main">
                        ${this.renderSidebarBefore?.()}
                        <main aria-label=${this.pageTitle} class="pf-c-sidebar__content">
                            <div class="pf-c-card">${this.renderTable()}</div>
                        </main>
                        ${this.renderSidebarAfter?.()}
                    </div>
                </div>
            </div>
            ${this.renderSectionAfter?.()}`;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: this.pageIcon,
            header: this.pageTitle,
            description: this.pageDescription,
        });
    }
}
