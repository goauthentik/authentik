import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BasePropertyMappingForm<T> extends ModelForm<T, string> {
    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated mapping.")
            : msg("Successfully created mapping.");
    }
}
