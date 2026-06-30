import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, TelegramSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-telegram-form")
export class PropertyMappingSourceTelegramForm extends BasePropertyMappingForm<TelegramSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<TelegramSourcePropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsSourceTelegramRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: TelegramSourcePropertyMapping): Promise<TelegramSourcePropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsSourceTelegramUpdate({
                pmUuid: this.instance.pk,
                telegramSourcePropertyMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsSourceTelegramCreate({
            telegramSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-telegram-form": PropertyMappingSourceTelegramForm;
    }
}
