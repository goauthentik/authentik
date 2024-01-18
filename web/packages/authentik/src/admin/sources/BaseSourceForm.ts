import { ModelForm } from "@goauthentik/elements/forms/ModelForm.js";

import { msg } from "@lit/localize";

export abstract class BaseSourceForm<T> extends ModelForm<T, string> {
    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated source.")
            : msg("Successfully created source.");
    }
}
