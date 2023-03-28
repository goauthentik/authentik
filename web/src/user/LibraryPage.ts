import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { LayoutType } from "@goauthentik/common/ui/config";
import { groupBy } from "@goauthentik/common/utils";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import "@goauthentik/user/LibraryApplication";
import Fuse from "fuse.js";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

import { Application, CoreApi } from "@goauthentik/api";

export function loading<T>(v: T, actual: TemplateResult): TemplateResult {
    if (!v) {
        return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
    }
    return actual;
}

@customElement("ak-library")
export class LibraryPage extends AKElement {
    @property({ attribute: false })
    apps?: PaginatedResponse<Application>;

    @state()
    selectedApp?: Application;

    @state()
    filteredApps: Application[] = [];

    @property()
    query = getURLParam<string | undefined>("search", undefined);

    fuse: Fuse<Application>;

    constructor() {
        super();
        this.fuse = new Fuse([], {
            keys: [
                { name: "name", weight: 3 },
                "slug",
                "group",
                { name: "metaDescription", weight: 0.5 },
                { name: "metaPublisher", weight: 0.5 },
            ],
            findAllMatches: true,
            includeScore: true,
            shouldSort: true,
            ignoreFieldNorm: true,
            useExtendedSearch: true,
            threshold: 0.5,
        });
        new CoreApi(DEFAULT_CONFIG).coreApplicationsList({}).then((apps) => {
            this.apps = apps;
            this.filteredApps = apps.results;
            this.fuse.setCollection(apps.results);
            if (!this.query) return;
            const matchingApps = this.fuse.search(this.query);
            if (matchingApps.length < 1) return;
            this.selectedApp = matchingApps[0].item;
            this.filteredApps = matchingApps.map((a) => a.item);
        });
    }

    pageTitle(): string {
        return t`My Applications`;
    }

    static get styles(): CSSResult[] {
        return [PFBase, PFDisplay, PFEmptyState, PFPage, PFContent, PFGrid, PFGallery].concat(css`
            :host,
            main {
                padding: 3% 5%;
            }
            .header {
                display: flex;
                flex-direction: row;
                justify-content: space-between;
            }
            .header input {
                width: 30ch;
                box-sizing: border-box;
                border: 0;
                border-bottom: 1px solid;
                border-bottom-color: #fd4b2d;
                background-color: transparent;
                font-size: 1.5rem;
            }
            .header input:focus {
                outline: 0;
            }
            .pf-c-page__main {
                overflow: hidden;
            }
            .pf-c-page__main-section {
                background-color: transparent;
            }
            .app-group-header {
                margin-bottom: 1em;
                margin-top: 1.2em;
            }
        `);
    }

    renderEmptyState(): TemplateResult {
        return html` <div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-cubes pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">${t`No Applications available.`}</h1>
                <div class="pf-c-empty-state__body">
                    ${t`Either no applications are defined, or you don't have access to any.`}
                </div>
            </div>
        </div>`;
    }

    filterApps(apps: Application[]): Application[] {
        return apps.filter((app) => {
            if (app.launchUrl && app.launchUrl !== "") {
                // If the launch URL is a full URL, only show with http or https
                if (app.launchUrl.indexOf("://") !== -1) {
                    return app.launchUrl.startsWith("http");
                }
                // If the URL doesn't include a protocol, assume its a relative path
                return true;
            }
            return false;
        });
    }

    getApps(): [string, Application[]][] {
        return groupBy(this.filterApps(this.filteredApps), (app) => app.group || "");
    }

    renderApps(): TemplateResult {
        let groupClass = "";
        let groupGrid = "";
        const uiConfig = rootInterface()?.uiConfig;
        switch (uiConfig?.layout.type) {
            case LayoutType.row:
                groupClass = "pf-m-12-col";
                groupGrid =
                    "pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-5-col-on-lg pf-m-all-2-col-on-xl";
                break;
            case LayoutType.column_2:
                groupClass = "pf-m-6-col";
                groupGrid =
                    "pf-m-all-12-col-on-sm pf-m-all-12-col-on-md pf-m-all-4-col-on-lg pf-m-all-4-col-on-xl";
                break;
            case LayoutType.column_3:
                groupClass = "pf-m-4-col";
                groupGrid =
                    "pf-m-all-12-col-on-sm pf-m-all-12-col-on-md pf-m-all-6-col-on-lg pf-m-all-6-col-on-xl";
                break;
        }
        return html`<div class="pf-l-grid pf-m-gutter">
            ${this.getApps().map(([group, apps]) => {
                return html`<div class="pf-l-grid__item ${groupClass}">
                    <div class="pf-c-content app-group-header">
                        <h2>${group}</h2>
                    </div>
                    <div class="pf-l-grid pf-m-gutter ${groupGrid}">
                        ${apps.map((app) => {
                            return html`<ak-library-app
                                class="pf-l-grid__item"
                                .application=${app}
                                background=${ifDefined(uiConfig?.theme.cardBackground)}
                                ?selected=${app.slug === this.selectedApp?.slug}
                            ></ak-library-app>`;
                        })}
                    </div>
                </div> `;
            })}
        </div>`;
    }

    resetSearch(): void {
        const searchInput = this.shadowRoot?.querySelector("input");
        if (searchInput) {
            searchInput.value = "";
        }
        this.query = "";
        updateURLParams({
            search: this.query,
        });
        this.selectedApp = undefined;
        this.filteredApps = this.apps?.results || [];
    }

    render(): TemplateResult {
        return html`<main role="main" class="pf-c-page__main" tabindex="-1" id="main-content">
            <div class="pf-c-content header">
                <h1>${t`My applications`}</h1>
                ${rootInterface()?.uiConfig?.enabledFeatures.search
                    ? html`<input
                          @input=${(ev: InputEvent) => {
                              this.query = (ev.target as HTMLInputElement).value;
                              if (this.query === "") {
                                  return this.resetSearch();
                              }
                              updateURLParams({
                                  search: this.query,
                              });
                              const apps = this.fuse.search(this.query);
                              if (apps.length < 1) return;
                              this.selectedApp = apps[0].item;
                              this.filteredApps = apps.map((a) => a.item);
                          }}
                          @keydown=${(ev: KeyboardEvent) => {
                              if (ev.key === "Enter" && this.selectedApp?.launchUrl) {
                                  window.location.assign(this.selectedApp.launchUrl);
                              } else if (ev.key === "Escape") {
                                  this.resetSearch();
                              }
                          }}
                          type="text"
                          class="pf-u-display-none pf-u-display-block-on-md"
                          autofocus
                          placeholder=${t`Search...`}
                          value=${ifDefined(this.query)}
                      />`
                    : html``}
            </div>
            <section class="pf-c-page__main-section">
                ${loading(
                    this.apps,
                    html`${this.filteredApps.length > 0
                        ? this.renderApps()
                        : this.renderEmptyState()}`,
                )}
            </section>
        </main>`;
    }
}
