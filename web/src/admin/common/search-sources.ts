/**
 * @file Search select sources for API objects chosen across the admin interface.
 */

import { aki } from "#common/api/client";
import { groupBy } from "#common/utils";

import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";

import {
    CoreApi,
    DeviceAccessGroup,
    EndpointsApi,
    Group,
    NotificationWebhookMapping,
    PoliciesApi,
    Policy,
    PropertymappingsApi,
    RbacApi,
    Role,
    User,
} from "@goauthentik/api";

import { html } from "lit";

export const policySource: SearchSelectSource<Policy> = {
    fetchObjects: (query) =>
        aki(PoliciesApi)
            .policiesAllList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (policy) => policy.pk,
    labelOf: (policy) => policy.name,
    groupBy: (policies) => groupBy(policies, (policy) => policy.verboseNamePlural),
};

export const groupSource: SearchSelectSource<Group> = {
    fetchObjects: (query) =>
        aki(CoreApi)
            .coreGroupsList(withQuery(query, { ordering: "name", includeUsers: false }))
            .then(({ results }) => results),
    keyOf: (group) => group.pk,
    labelOf: (group) => group.name,
};

export const userSource: SearchSelectSource<User> = {
    fetchObjects: (query) =>
        aki(CoreApi)
            .coreUsersList(withQuery(query, { ordering: "username" }))
            .then(({ results }) => results),
    keyOf: (user) => String(user.pk),
    labelOf: (user) => user.username,
    describe: (user) => html`${user.name}`,
};

export const deviceAccessGroupSource: SearchSelectSource<DeviceAccessGroup> = {
    fetchObjects: (query) =>
        aki(EndpointsApi)
            .endpointsDeviceAccessGroupsList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (group) => group.pbmUuid,
    labelOf: (group) => group.name,
};

export const roleSource: SearchSelectSource<Role> = {
    fetchObjects: (query) =>
        aki(RbacApi)
            .rbacRolesList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (role) => role.pk,
    labelOf: (role) => role.name,
};

export const notificationMappingSource: SearchSelectSource<NotificationWebhookMapping> = {
    fetchObjects: (query) =>
        aki(PropertymappingsApi)
            .propertymappingsNotificationList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (mapping) => mapping.pk,
    labelOf: (mapping) => mapping.name,
};
