import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { customElement } from "lit/decorators.js";

import { NotificationWebhookMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-notification-form")
export class PropertyMappingNotification extends ModelForm<NotificationWebhookMapping, string> {
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
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationCreate({
                notificationWebhookMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-notification-form": PropertyMappingNotification;
    }
}
