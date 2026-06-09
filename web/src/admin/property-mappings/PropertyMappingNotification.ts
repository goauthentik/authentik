import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { NotificationWebhookMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-notification-form")
export class PropertyMappingNotification extends BasePropertyMappingForm<NotificationWebhookMapping> {
    loadInstance(pk: string): Promise<NotificationWebhookMapping> {
        return aki(PropertymappingsApi).propertymappingsNotificationRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: NotificationWebhookMapping): Promise<NotificationWebhookMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsNotificationUpdate({
                pmUuid: this.instance.pk,
                notificationWebhookMappingRequest: data,
            });
        }
        return aki(PropertymappingsApi).propertymappingsNotificationCreate({
            notificationWebhookMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-notification-form": PropertyMappingNotification;
    }
}
