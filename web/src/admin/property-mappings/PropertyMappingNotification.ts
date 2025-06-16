import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";

import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { NotificationWebhookMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

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
                pmUuid: this.instance.pk,
                notificationWebhookMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationCreate({
            notificationWebhookMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-notification-form": PropertyMappingNotification;
    }
}
