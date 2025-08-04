import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BaseStageForm<T> extends ModelForm<T, string> {
    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated stage.")
            : msg("Successfully created stage.");
    }
}
