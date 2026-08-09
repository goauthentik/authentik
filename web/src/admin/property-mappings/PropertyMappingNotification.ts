import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { NotificationWebhookMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-notification-form")
export class PropertyMappingNotification extends BasePropertyMappingForm<NotificationWebhookMapping> {
    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsNotificationRetrieve({ pmUuid: pk }),
        create: (notificationWebhookMappingRequest: NotificationWebhookMapping) =>
            aki(PropertymappingsApi).propertymappingsNotificationCreate({
                notificationWebhookMappingRequest,
            }),
        update: (pk: string, notificationWebhookMappingRequest: NotificationWebhookMapping) =>
            aki(PropertymappingsApi).propertymappingsNotificationUpdate({
                pmUuid: pk,
                notificationWebhookMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-notification-form": PropertyMappingNotification;
    }
}
