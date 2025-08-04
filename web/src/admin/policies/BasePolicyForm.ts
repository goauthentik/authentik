import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BasePolicyForm<T> extends ModelForm<T, string> {
    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated policy.")
            : msg("Successfully created policy.");
    }
}
