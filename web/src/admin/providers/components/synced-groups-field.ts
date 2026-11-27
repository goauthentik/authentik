import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { DualSelectPair } from "#elements/ak-dual-select/types";
import { LitFC } from "#elements/types";

import { CoreApi, Group } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

const groupToSelect = (group: Group): DualSelectPair<Group> => [
    group.pk,
    group.name,
    group.name,
    group,
];

async function groupsProvider(page = 1, search = "") {
    const groups = await aki(CoreApi).coreGroupsList({
        ordering: "name",
        includeUsers: false,
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: groups.pagination,
        options: groups.results.map(groupToSelect),
    };
}

function groupsSelector(instanceGroups: string[] | undefined) {
    if (!instanceGroups) {
        return async () => [];
    }

    return async () => {
        const groups = await Promise.allSettled(
            instanceGroups.map((groupId) =>
                aki(CoreApi).coreGroupsRetrieve({ groupUuid: groupId }),
            ),
        );

        return groups
            .filter(
                (result): result is PromiseFulfilledResult<Group> => result.status === "fulfilled",
            )
            .map((result) => groupToSelect(result.value));
    };
}

export interface SyncedGroupsFieldProps {
    /**
     * The primary keys of the groups the provider currently syncs.
     */
    groupFilters?: string[];
}

/**
 * The groups an outgoing sync provider (SCIM, Google Workspace, Entra ID) syncs.
 *
 * This only scopes groups. Which users sync is decided by access to the provider's application.
 */
export const AKSyncedGroupsField: LitFC<SyncedGroupsFieldProps> = ({ groupFilters }) =>
    html`<ak-form-element-horizontal label=${msg("Group Filter")} name="groupFilters">
        <ak-dual-select-dynamic-selected
            .provider=${groupsProvider}
            .selector=${groupsSelector(groupFilters)}
            available-label=${msg("Available Groups")}
            selected-label=${msg("Selected Groups")}
        ></ak-dual-select-dynamic-selected>
        <p class="pf-c-form__helper-text">
            ${msg("Groups to be synced. If empty, all groups will be synced.")}
        </p>
    </ak-form-element-horizontal>`;
