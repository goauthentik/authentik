import "@goauthentik/elements/PageHeader";
import { updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import { Table } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFSidebar from "@patternfly/patternfly/components/Sidebar/sidebar.css";

export abstract class TablePage<T> extends Table<T> {
    abstract pageTitle(): string;
    abstract pageDescription(): string | undefined;
    abstract pageIcon(): string;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFPage, PFContent, PFSidebar);
    }

    constructor() {
        super();
        this.dataset.akApiTable = "true";
    }

    renderSidebarBefore(): TemplateResult {
        return html``;
    }

    renderSidebarAfter(): TemplateResult {
        return html``;
    }

    // Optionally render section above the table
    renderSectionBefore(): TemplateResult {
        return html``;
    }

    // Optionally render section below the table
    renderSectionAfter(): TemplateResult {
        return html``;
    }

    renderEmpty(inner?: TemplateResult): TemplateResult {
        return super.renderEmpty(html`
            ${inner
                ? inner
                : html`<ak-empty-state icon=${this.pageIcon()} header="${msg("No objects found.")}">
                      <div slot="body">
                          ${this.searchEnabled() ? this.renderEmptyClearSearch() : html``}
                      </div>
                      <div slot="primary">${this.renderObjectCreate()}</div>
                  </ak-empty-state>`}
        `);
    }

    renderEmptyClearSearch(): TemplateResult {
        if (this.search === "") {
            return html``;
        }
        return html`<button
            @click=${() => {
                this.search = "";
                this.requestUpdate();
                this.fetch();
                updateURLParams({
                    search: "",
                });
            }}
            class="pf-c-button pf-m-link"
        >
            ${msg("Clear search")}
        </button>`;
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon=${this.pageIcon()}
                header=${this.pageTitle()}
                description=${ifDefined(this.pageDescription())}
            >
            </ak-page-header>
            ${this.renderSectionBefore()}
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-c-sidebar pf-m-gutter">
                    <div class="pf-c-sidebar__main">
                        ${this.renderSidebarBefore()}
                        <div class="pf-c-sidebar__content">
                            <div class="pf-c-card">${this.renderTable()}</div>
                        </div>
                        ${this.renderSidebarAfter()}
                    </div>
                </div>
            </section>
            ${this.renderSectionAfter()}`;
    }
}

// This painstakingly researched path is nonetheless surprisingly robust; it works for every extant
// TablePage, but only because Jens has been utterly consistent in where he puts his TablePage
// elements with respect to the Interface object.  If we ever re-arrange this code, we're going
// to have to re-arrange this as well.

export function findTable<T, U extends TablePage<T>>(): U | undefined {
    return (
        (document.body
            ?.querySelector("[data-ak-interface-root]")
            ?.shadowRoot?.querySelector("ak-locale-context")
            ?.querySelector("ak-router-outlet")
            ?.shadowRoot?.querySelector("[data-ak-api-table]") as U) ?? undefined
    );
}
