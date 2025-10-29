import type { AppGroupEntry } from "./types.js";

import { rootInterface } from "#common/theme";
import { LayoutType } from "#common/ui/config";

import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { UserInterface } from "#user/index.entrypoint";
import { AKLibraryApp } from "#user/LibraryApplication/index";

import { ApplicationRoute } from "#admin/Routes";

import { Application } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { kebabCase } from "change-case";
import { HTMLAttributes } from "react";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { RefOrCallback } from "lit/directives/ref.js";
import { repeat } from "lit/directives/repeat.js";

const LayoutColumnCount = {
    [LayoutType.row]: 1,
    [LayoutType.column_2]: 2,
    [LayoutType.column_3]: 3,
} as const satisfies Record<LayoutType, number>;

export interface AKLibraryApplicationListProps extends HTMLAttributes<HTMLDivElement> {
    groupedApps: AppGroupEntry[];
    layout: LayoutType;
    background?: string | null;
    selectedApp?: Application | null;
    targetRef?: RefOrCallback | null;
}

/**
 * Renders the current library list of a User's Applications.
 */
export const AKLibraryApplicationList: LitFC<AKLibraryApplicationListProps> = ({
    groupedApps,
    layout = LayoutType.row,
    background,
    selectedApp,
    targetRef,
    ...props
}) => {
    const columnCount = LayoutColumnCount[layout] ?? 1;
    const { me, uiConfig } = rootInterface<UserInterface>();
    const canEdit = !!(uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser);

    return html`<div
        role="presentation"
        part="app-list"
        style="--app-list-column-count: ${columnCount}"
        ${spread(props)}
    >
        ${repeat(
            groupedApps,
            ([groupLabel]) => groupLabel,
            ([groupLabel, apps], groupIndex) => {
                const groupID = kebabCase(groupLabel);
                const activeDescendantID =
                    selectedApp && apps.includes(selectedApp) ? `app-${selectedApp.pk}` : nothing;

                return html`<fieldset
                    data-group-id=${ifPresent(groupID)}
                    part="app-group"
                    data-group-index=${groupIndex}
                    data-app-count=${apps.length}
                    aria-activedescendant=${activeDescendantID}
                >
                    <legend
                        class="pf-c-content ${!groupLabel ? "less-contrast-sr-only" : ""}"
                        part="app-group-header"
                    >
                        <h2 id=${`app-group-${groupID}`}>${groupLabel || msg("Ungrouped")}</h2>
                    </legend>
                    ${repeat(
                        apps,
                        (application) => application.pk,
                        (application, appIndex) => {
                            const selected = selectedApp === application;

                            const editURL = canEdit
                                ? ApplicationRoute.EditURL(application.slug)
                                : null;

                            return AKLibraryApp({
                                application,
                                appIndex,
                                groupIndex,
                                background,
                                editURL,
                                "targetRef": selected ? targetRef : null,
                                "aria-selected": selected,
                            });
                        },
                    )}
                    <hr part="app-group-separator" aria-hidden="true" />
                </fieldset>`;
            },
        )}
    </div>`;
};
