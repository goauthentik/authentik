import Styles from "./ak-library-application-list.styles.css";
import type { AppGroupEntry } from "./types.js";

import { LayoutType } from "#common/ui/config";

import { AKElement } from "#elements/Base";
import { ifPresent } from "#elements/utils/attributes";

import { AKLibraryApp } from "#user/LibraryApplication/index";

import { kebabCase } from "change-case";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const LayoutColumnCount = {
    [LayoutType.row]: 1,
    [LayoutType.column_2]: 2,
    [LayoutType.column_3]: 3,
} as const satisfies Record<LayoutType, number>;

/**
 * @element ak-library-application-list
 * @class LibraryPageApplicationList
 *
 * Renders the current library list of a User's Applications.
 *
 */
@customElement("ak-library-application-list")
export class LibraryPageApplicationList extends AKElement {
    static styles = [
        // ---
        PFBase,
        PFEmptyState,
        PFContent,
        PFGrid,
        PFButton,
        PFCard,
        Styles,
    ];

    @property({ attribute: true })
    public layout: LayoutType = LayoutType.row;

    @property({ attribute: true })
    public background: string | null = null;

    @property({ attribute: true })
    public selected: string | null = null;

    @property({ attribute: false })
    public apps: AppGroupEntry[] = [];

    render() {
        // const [groupClass, groupGrid] = LayoutClasses[this.layout] || LayoutClasses[LayoutType.row];
        // const [groupClass, groupGrid] = LayoutClasses[LayoutType.column_2];

        return html`<div
            part="app-list"
            style="--app-list-column-count: ${LayoutColumnCount[LayoutType.column_2] ?? 1}"
            role="grid"
            aria-label=${msg("Available applications")}
        >
            ${repeat(
                this.apps,
                ([groupLabel]) => groupLabel,
                ([groupLabel, apps], idx) => {
                    return html`<div
                        role="rowgroup"
                        data-group-id=${ifPresent(kebabCase(groupLabel))}
                        aria-labelledby="app-group-${idx}"
                        part="app-group"
                    >
                        <div class="pf-c-content" part="app-group-header">
                            <h2 id="app-group-${idx}">${groupLabel}</h2>
                        </div>
                        ${repeat(
                            apps,
                            (app) => app.pk,
                            (app) =>
                                AKLibraryApp({
                                    part: "app-card",
                                    application: app,
                                    background: this.background,
                                    selected: app.slug === this.selected,
                                }),
                        )}
                    </div> `;
                },
            )}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-application-list": LibraryPageApplicationList;
    }
}
