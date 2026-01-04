import { APIError } from "#common/errors/network";
import { APIMessage, MessageLevel } from "#common/messages";

import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BaseProviderForm<T> extends ModelForm<T, number> {
    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated provider.")
            : msg("Successfully created provider.");
    }

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
