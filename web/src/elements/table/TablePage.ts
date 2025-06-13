import "#components/ak-page-header";
import { updateURLParams } from "#elements/router/RouteMatch";
import { Table } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { CSSResult, nothing } from "lit";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFSidebar from "@patternfly/patternfly/components/Sidebar/sidebar.css";

export abstract class TablePage<T extends object> extends Table<T> {
    static styles: CSSResult[] = [...super.styles, PFPage, PFContent, PFSidebar];

    //#region Abstract methods

    /**
     * The title of the page.
     * @abstract
     */
    abstract pageTitle(): string;

    /**
     * The description of the page.
     * @abstract
     */
    abstract pageDescription(): string | undefined;

    /**
     * The icon to display in the page header.
     * @abstract
     */
    abstract pageIcon(): string;

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

    /**
     * Render the empty state.
     */
    protected renderEmpty(inner?: TemplateResult): TemplateResult {
        return super.renderEmpty(html`
            ${inner
                ? inner
                : html`<ak-empty-state icon=${this.pageIcon()} header="${msg("No objects found.")}">
                      <div slot="body">
                          ${this.searchEnabled() ? this.renderEmptyClearSearch() : nothing}
                      </div>
                      <div slot="primary">${this.renderObjectCreate()}</div>
                  </ak-empty-state>`}
        `);
    }

    protected clearSearch = () => {
        this.search = "";

        this.requestUpdate();

        updateURLParams({
            search: "",
        });

        return this.fetch();
    };

    protected renderEmptyClearSearch(): SlottedTemplateResult {
        if (!this.search) {
            return nothing;
        }

        return html`<button @click=${this.clearSearch} class="pf-c-button pf-m-link">
            ${msg("Clear search")}
        </button>`;
    }

    render() {
        return html`<ak-page-header
                icon=${this.pageIcon()}
                header=${this.pageTitle()}
                description=${ifDefined(this.pageDescription())}
            >
            </ak-page-header>
            ${this.renderSectionBefore?.()}
            <section
                id="table-page-main"
                aria-label=${this.pageTitle()}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-sidebar pf-m-gutter">
                    <div class="pf-c-sidebar__main">
                        ${this.renderSidebarBefore?.()}
                        <div class="pf-c-sidebar__content">
                            <div class="pf-c-card">${this.renderTable()}</div>
                        </div>
                        ${this.renderSidebarAfter?.()}
                    </div>
                </div>
            </section>
            ${this.renderSectionAfter?.()}`;
    }
}
