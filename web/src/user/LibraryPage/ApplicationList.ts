import { PFSize } from "@goauthentik/common/enums.js";
import { LayoutType } from "@goauthentik/common/ui/config";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { Application } from "@goauthentik/api";

import type { AppGroupEntry, AppGroupList } from "./types";

type Pair = [string, string];

// prettier-ignore
const LAYOUTS = new Map<string, [string, string]>([
    [
        "row",
        ["pf-m-12-col", "pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-5-col-on-lg pf-m-all-2-col-on-xl"]],
    [
        "2-column",
        ["pf-m-6-col", "pf-m-all-12-col-on-sm pf-m-all-12-col-on-md pf-m-all-4-col-on-lg pf-m-all-4-col-on-xl"],
    ],
    [
        "3-column",
        ["pf-m-4-col", "pf-m-all-12-col-on-sm pf-m-all-12-col-on-md pf-m-all-6-col-on-lg pf-m-all-6-col-on-xl"],
    ],
]);

@customElement("ak-library-application-list")
export class LibraryPageApplicationList extends AKElement {
    static get styles() {
        return [
            PFBase,
            PFTable,
            PFButton,
            PFEmptyState,
            css`
                .app-row a {
                    font-weight: bold;
                }
            `,
        ];
    }

    @property({ attribute: true })
    layout = "row" as LayoutType;

    @property({ attribute: true })
    background: string | undefined = undefined;

    @property({ attribute: true })
    selected = "";

    @property({ attribute: false })
    apps: AppGroupList = [];

    expanded = new Set<string>();

    get currentLayout(): Pair {
        const layout = LAYOUTS.get(this.layout);
        if (!layout) {
            console.warn(`Unrecognized layout: ${this.layout || "-undefined-"}`);
            return LAYOUTS.get("row") as Pair;
        }
        return layout;
    }

    render() {
        const canEdit =
            rootInterface()?.uiConfig?.enabledFeatures.applicationEdit &&
            rootInterface()?.me?.user.isSuperuser;

        const toggleExpansion = (pk: string) => {
            if (this.expanded.has(pk)) {
                this.expanded.delete(pk);
            } else {
                this.expanded.add(pk);
            }
            this.requestUpdate();
        };

        const [groupClass, groupGrid] = this.currentLayout;

        const expandedClass = (pk: string) => ({
            "pf-m-expanded": this.expanded.has(pk),
        });

        const renderExpansionCell = (app: Application) =>
            app.metaDescription
                ? html`<td class="pf-c-table__toggle" role="cell">
                      <button
                          class="pf-c-button pf-m-plain ${classMap(expandedClass(app.pk))}"
                          @click=${() => toggleExpansion(app.pk)}
                      >
                          <div class="pf-c-table__toggle-icon">
                              &nbsp;<i class="fas fa-angle-down" aria-hidden="true"></i>&nbsp;
                          </div>
                      </button>
                  </td>`
                : nothing;

        const renderAppIcon = (app: Application) =>
            html`<a
                href="${ifDefined(app.launchUrl ?? "")}"
                target="${ifDefined(app.openInNewTab ? "_blank" : undefined)}"
            >
                <ak-app-icon size=${PFSize.Small} .app=${app}></ak-app-icon>
            </a>`;

        const renderAppUrl = (app: Application) =>
            app.launchUrl === "goauthentik.io://providers/rac/launch"
                ? html`<ak-library-rac-endpoint-launch .app=${app}>
                      <a slot="trigger"> ${app.name} </a>
                  </ak-library-rac-endpoint-launch>`
                : html`<a
                      href="${ifDefined(app.launchUrl ?? "")}"
                      target="${ifDefined(app.openInNewTab ? "_blank" : undefined)}"
                      >${app.name}</a
                  >`;

        const renderAppDescription = (app: Application) =>
            app.metaDescription
                ? html` <tr
                      class="pf-c-table__expandable-row ${classMap(expandedClass(app.pk))}"
                      role="row"
                  >
                      <td></td>
                      <td></td>
                      <td colspan="3">${app.metaDescription}</td>
                  </tr>`
                : nothing;

        const renderGroup = ([group, apps]: AppGroupEntry) => html`
            ${group
                ? html`<tr>
                      <td colspan="5"><h2>${group}</h2></td>
                  </tr>`
                : nothing}
            ${apps.map(
                (app: Application) =>
                    html`<tr>
                            <td>${renderExpansionCell(app)}</td>
                            <td>${renderAppIcon(app)}</td>
                            <td class="app-row">${renderAppUrl(app)}</td>
                            <td>${app.metaPublisher ?? ""}</td>
                            <td>
                                <a
                                    class="pf-c-button pf-m-control pf-m-small pf-m-block"
                                    href="/if/admin/#/core/applications/${app?.slug}"
                                >
                                    <i class="fas fa-edit"></i>&nbsp;${msg("Edit")}
                                </a>
                            </td>
                        </tr>
                        ${this.expanded.has(app.pk) ? renderAppDescription(app) : nothing} `,
            )}
        `;

        return html`<table class="pf-c-table pf-m-compact pf-m-grid-sm pf-m-expandable">
            <thead>
                <tr role="row">
                    <th></th>
                    <th></th>
                    <th>${msg("Application")}</th>
                    <th>${msg("Publisher")}</th>
                    ${canEdit ? html`<th>${msg("Edit")}</th>` : nothing}
                </tr>
            </thead>
            <tbody>
                ${this.apps.map(renderGroup)}
            </tbody>
        </table> `;
    }
}
