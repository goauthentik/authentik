import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BaseStageForm<T> extends ModelForm<T, string> {
    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated stage.")
            : msg("Successfully created stage.");
    }
}
