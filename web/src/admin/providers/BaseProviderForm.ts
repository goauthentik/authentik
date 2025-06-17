import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BaseProviderForm<T> extends ModelForm<T, number> {
    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated provider.")
            : msg("Successfully created provider.");
    }
}
