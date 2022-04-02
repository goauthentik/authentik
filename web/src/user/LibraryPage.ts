import Fuse from "fuse.js";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "../authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

import { Application, CoreApi } from "@goauthentik/api";

import { AKResponse } from "../api/Client";
import { DEFAULT_CONFIG } from "../api/Config";
import { UIConfig, uiConfig } from "../common/config";
import { getURLParam, updateURLParams } from "../elements/router/RouteMatch";
import { groupBy, loading } from "../utils";
import "./LibraryApplication";

@customElement("ak-library")
export class LibraryPage extends LitElement {
    @property({ attribute: false })
    apps?: AKResponse<Application>;

    @property({ attribute: false })
    selectedApp?: Application;

    @property()
    query = getURLParam<string | undefined>("search", undefined);

    fuse?: Fuse<Application>;

    constructor() {
        super();
        new CoreApi(DEFAULT_CONFIG).coreApplicationsList({}).then((apps) => {
            this.apps = apps;
            this.fuse = new Fuse(apps.results, {
                keys: ["slug", "name", "metaDescription", "metaPublisher", "group"],
            });
            if (!this.fuse || !this.query) return;
            const matchingApps = this.fuse.search(this.query);
            if (matchingApps.length < 1) return;
            this.selectedApp = matchingApps[0].item;
        });
    }

    pageTitle(): string {
        return t`My Applications`;
    }

    static get styles(): CSSResult[] {
        return [PFBase, PFDisplay, PFEmptyState, PFPage, PFContent, PFGrid, PFGallery, AKGlobal]
            .concat(css`
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

    getApps(): [string, Application[]][] {
        return groupBy(
            this.apps?.results.filter((app) => {
                if (app.launchUrl) {
                    // If the launch URL is a full URL, only show with http or https
                    if (app.launchUrl.indexOf("://") !== -1) {
                        return app.launchUrl.startsWith("http");
                    }
                    // If the URL doesn't include a protocol, assume its a relative path
                    return true;
                }
                return false;
            }) || [],
            (app) => app.group || "",
        );
    }

    renderApps(config: UIConfig): TemplateResult {
        return html`${this.getApps().map(([group, apps]) => {
            return html`
                <div class="pf-c-content app-group-header">
                    <h2>${group}</h2>
                </div>
                <div
                    class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-5-col-on-lg pf-m-all-3-col-on-xl"
                >
                    ${apps.map((app) => {
                        return html`<ak-library-app
                            class="pf-l-grid__item"
                            .application=${app}
                            background=${config.color.cardBackground}
                            ?selected=${app.slug === this.selectedApp?.slug}
                        ></ak-library-app>`;
                    })}
                </div>
            `;
        })}`;
    }

    render(): TemplateResult {
        return html`${until(
            uiConfig().then((config) => {
                return html`<main
                    role="main"
                    class="pf-c-page__main"
                    tabindex="-1"
                    id="main-content"
                >
                    <div class="pf-c-content header">
                        <h1>${t`My applications`}</h1>
                        ${config.enabledFeatures.search
                            ? html`<input
                                  @input=${(ev: InputEvent) => {
                                      this.query = (ev.target as HTMLInputElement).value;
                                      updateURLParams({
                                          search: this.query,
                                      });
                                      if (!this.fuse) return;
                                      const apps = this.fuse.search(this.query);
                                      if (apps.length < 1) return;
                                      this.selectedApp = apps[0].item;
                                  }}
                                  @keydown=${(ev: KeyboardEvent) => {
                                      if (ev.key === "Enter" && this.selectedApp?.launchUrl) {
                                          window.location.assign(this.selectedApp.launchUrl);
                                      } else if (ev.key === "Escape") {
                                          (ev.target as HTMLInputElement).value = "";
                                          this.query = "";
                                          updateURLParams({
                                              search: this.query,
                                          });
                                          this.selectedApp = undefined;
                                      }
                                  }}
                                  type="text"
                                  class="pf-u-display-none pf-u-display-block-on-md"
                                  autofocus
                                  placeholder=${t`Search...`}
                              />`
                            : html``}
                    </div>
                    <section class="pf-c-page__main-section">
                        ${loading(
                            this.apps,
                            html`${(this.apps?.results || []).filter((app) => {
                                return app.launchUrl !== null;
                            }).length > 0
                                ? this.renderApps(config)
                                : this.renderEmptyState()}`,
                        )}
                    </section>
                </main>`;
            }),
        )}`;
    }
}
