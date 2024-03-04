import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { customElement } from "lit/decorators.js";

import { NotificationWebhookMapping, PropertymappingsApi } from "@goauthentik/api";

import { BasePropertyMappingForm } from "./BasePropertyMappingForm";

@customElement("ak-property-mapping-notification-form")
export class PropertyMappingNotification extends BasePropertyMappingForm<NotificationWebhookMapping> {
    loadInstance(pk: string): Promise<NotificationWebhookMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: NotificationWebhookMapping): Promise<NotificationWebhookMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationUpdate({
                pmUuid: this.instance.pk || "",
                notificationWebhookMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationCreate({
                notificationWebhookMappingRequest: data,
            });
        }
    }
}
