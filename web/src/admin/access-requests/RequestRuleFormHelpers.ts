import { aki } from "#common/api/client";

import { DualSelectPair, DualSelectPairSource } from "#elements/ak-dual-select/types";

import {
    Application,
    ApplicationEntitlement,
    CoreApi,
    Group,
    RequestableTarget,
    User,
} from "@goauthentik/api";

const groupToSelect = (group: Group): DualSelectPair<Group> => [
    group.pk,
    group.name,
    group.name,
    group,
];

export async function reviewerGroupsProvider(page = 1, search = "") {
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

export function reviewerGroupsSelector(instanceGroups: string[] | undefined): DualSelectPairSource {
    if (!instanceGroups) {
        return async () => [];
    }

    return async () => {
        const groups = await Promise.allSettled(
            instanceGroups.map((groupUuid) => aki(CoreApi).coreGroupsRetrieve({ groupUuid })),
        );

        return groups
            .filter((g) => g.status === "fulfilled")
            .map((g) => g.value)
            .map(groupToSelect);
    };
}

const userToSelect = (user: User): DualSelectPair<User> => [
    user.pk,
    user.username,
    user.username,
    user,
];

export async function reviewerUsersProvider(page = 1, search = "") {
    const users = await aki(CoreApi).coreUsersList({
        ordering: "username",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: users.pagination,
        options: users.results.map(userToSelect),
    };
}

export function reviewerUsersSelector(instanceUsers: number[] | undefined): DualSelectPairSource {
    if (!instanceUsers) {
        return async () => [];
    }

    return async () => {
        const users = await Promise.allSettled(
            instanceUsers.map((id) => aki(CoreApi).coreUsersRetrieve({ id })),
        );

        return users
            .filter((u) => u.status === "fulfilled")
            .map((u) => u.value)
            .map(userToSelect);
    };
}

const appToSelect = (app: Application): DualSelectPair<Application> => [
    app.pbmUuid,
    app.name,
    app.name,
    app,
];

export async function pbmApplicationsProvider(page = 1, search = "") {
    const apps = await aki(CoreApi).coreApplicationsList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        superuserFullList: true,
        page,
    });

    return {
        pagination: apps.pagination,
        options: apps.results.map(appToSelect),
    };
}

/**
 * Pre-selects the rule's existing Application targets on edit (derived from `pbmTargets`,
 * which already carries the resolved parent - no extra API calls needed), or falls back to
 * `fallbackApp` on create (the Application the form was opened from - see
 * PolicyBindingModelRequestRuleForm). There's no API to look an Application up by pbmUuid
 * alone (its detail route is keyed by slug), so the caller passes the object it already has
 * rather than this helper re-fetching it.
 */
export function pbmApplicationsSelector(
    pbmTargets: RequestableTarget[] | undefined,
    fallbackApp: Application | undefined,
): DualSelectPairSource {
    return async () => {
        if (pbmTargets) {
            return pbmTargets
                .filter((target) => target.parent.pbmUuid === target.pbmUuid)
                .map((target) => appToSelect(target.parent));
        }
        return fallbackApp ? [appToSelect(fallbackApp)] : [];
    };
}

const entitlementToSelect = (
    entitlement: ApplicationEntitlement,
): DualSelectPair<ApplicationEntitlement> => [
    entitlement.pbmUuid,
    entitlement.name,
    entitlement.name,
    entitlement,
];

export async function pbmEntitlementsProvider(page = 1, search = "") {
    const entitlements = await aki(CoreApi).coreApplicationEntitlementsList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: entitlements.pagination,
        options: entitlements.results.map(entitlementToSelect),
    };
}

/**
 * Pre-selects the rule's existing Entitlement targets on edit, derived from `pbmTargets` the
 * same way pbmApplicationsSelector does. No create-mode fallback: the form is only ever opened
 * with an Application pbmUuid today.
 */
export function pbmEntitlementsSelector(
    pbmTargets: RequestableTarget[] | undefined,
): DualSelectPairSource {
    if (!pbmTargets) {
        return async () => [];
    }

    return async () => {
        return pbmTargets
            .filter((target) => target.parent.pbmUuid !== target.pbmUuid)
            .map((target) => [target.pbmUuid, target.label, target.label]);
    };
}
