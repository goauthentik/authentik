import { t } from "@lingui/macro";

import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFSidebar from "@patternfly/patternfly/components/Sidebar/sidebar.css";

import "../../elements/PageHeader";
import { updateURLParams } from "../router/RouteMatch";
import { Table } from "./Table";

export abstract class TablePage<T> extends Table<T> {
    abstract pageTitle(): string;
    abstract pageDescription(): string | undefined;
    abstract pageIcon(): string;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFPage, PFContent, PFSidebar);
    }

    renderSidebarBefore(): TemplateResult {
        return html``;
    }

    renderSidebarAfter(): TemplateResult {
        return html``;
    }

    renderEmpty(inner?: TemplateResult): TemplateResult {
        return super.renderEmpty(html`
            ${inner
                ? inner
                : html`<ak-empty-state icon=${this.pageIcon()} header="${t`No objects found.`}">
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
            ${t`Clear search`}
        </button>`;
    }

    renderObjectCreate(): TemplateResult {
        return html``;
    }

    renderToolbar(): TemplateResult {
        return html`${this.renderObjectCreate()}${super.renderToolbar()}`;
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon=${this.pageIcon()}
                header=${this.pageTitle()}
                description=${ifDefined(this.pageDescription())}
            >
            </ak-page-header>
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
            </section>`;
    }
}
