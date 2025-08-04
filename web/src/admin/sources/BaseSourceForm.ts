import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BaseSourceForm<T> extends ModelForm<T, string> {
    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated source.")
            : msg("Successfully created source.");
    }
}
