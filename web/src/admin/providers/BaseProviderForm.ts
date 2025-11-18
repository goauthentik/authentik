import { APIError } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { ModelForm } from "#elements/forms/ModelForm";
import { APIMessage } from "#elements/messages/Message";

import { msg } from "@lit/localize";

export abstract class BaseProviderForm<T> extends ModelForm<T, number> {
    protected override entityLabel = msg("Provider", { id: "entity.provider.singular" });

    protected override formatAPIErrorMessage(error: APIError): APIMessage {
        return {
            level: MessageLevel.error,
            ...super.formatAPIErrorMessage(error),
            message: this.instance
                ? msg("An error occurred while updating the provider.")
                : msg("An error occurred while creating the provider."),
        };
    }
}
