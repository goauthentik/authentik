import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BaseSourceForm<T> extends ModelForm<T, string> {
    /**
     * Success message to display after a successful form submission.
     */
    public getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated source.")
            : msg("Successfully created source.");
    }
}
