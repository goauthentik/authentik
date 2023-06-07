import { LayoutType } from "@goauthentik/common/ui/config";
import { AKElement } from "@goauthentik/elements/Base";

import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
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

const styles = [
    PFBase,
    PFEmptyState,
    PFContent,
    PFGrid,
    css`
        .app-group-header {
            margin-bottom: 1em;
            margin-top: 1.2em;
        }
    `,
];

@customElement("ak-library-application-list")
export class LibraryPageApplicationList extends AKElement {
    static styles = styles;

    @property({ attribute: true })
    layout = "row" as LayoutType;

    @property({ attribute: true })
    background: string | undefined = undefined;

    @property({ attribute: true })
    selected = "";

    @property({ attribute: false })
    apps: AppGroupList = [];

    get currentLayout(): Pair {
        const layout = LAYOUTS.get(this.layout);
        if (!layout) {
            console.warn(`Unrecognized layout: ${this.layout || "-undefined-"}`);
            return LAYOUTS.get("row") as Pair;
        }
        return layout;
    }

    render() {
        const [groupClass, groupGrid] = this.currentLayout;

        return html`<div class="pf-l-grid pf-m-gutter">
            ${this.apps.map(([group, apps]: AppGroupEntry) => {
                return html`<div class="pf-l-grid__item ${groupClass}">
                    <div class="pf-c-content app-group-header">
                        <h2>${group}</h2>
                    </div>
                    <div class="pf-l-grid pf-m-gutter ${groupGrid}">
                        ${apps.map((app: Application) => {
                            return html`<ak-library-app
                                class="pf-l-grid__item"
                                .application=${app}
                                background=${ifDefined(this.background)}
                                ?selected=${app.slug === this.selected}
                            ></ak-library-app>`;
                        })}
                    </div>
                </div> `;
            })}
        </div>`;
    }
}
