import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, TelegramSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-telegram-form")
export class PropertyMappingSourceTelegramForm extends BasePropertyMappingForm<TelegramSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourceTelegramRetrieve({ pmUuid: pk }),
        create: (telegramSourcePropertyMappingRequest: TelegramSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceTelegramCreate({
                telegramSourcePropertyMappingRequest,
            }),
        update: (pk: string, telegramSourcePropertyMappingRequest: TelegramSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceTelegramUpdate({
                pmUuid: pk,
                telegramSourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-telegram-form": PropertyMappingSourceTelegramForm;
    }
}
