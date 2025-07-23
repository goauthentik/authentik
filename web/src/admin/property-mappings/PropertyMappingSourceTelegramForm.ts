import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, TelegramSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-telegram-form")
export class PropertyMappingSourceTelegramForm extends BasePropertyMappingForm<TelegramSourcePropertyMapping> {
    docLink(): string {
        return "/docs/users-sources/sources/property-mappings/expressions?utm_source=authentik";
    }

    loadInstance(pk: string): Promise<TelegramSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceTelegramRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: TelegramSourcePropertyMapping): Promise<TelegramSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceTelegramUpdate({
                pmUuid: this.instance.pk,
                telegramSourcePropertyMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceTelegramCreate({
            telegramSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-telegram-form": PropertyMappingSourceTelegramForm;
    }
}
