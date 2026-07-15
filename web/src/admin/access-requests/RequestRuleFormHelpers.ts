import { aki } from "#common/api/client";

import { DualSelectPair, DualSelectPairSource } from "#elements/ak-dual-select/types";

import { CoreApi, Group, User } from "@goauthentik/api";

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
