import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BasePolicyForm<T extends object> extends ModelForm<T, string> {
    public static override verboseName = msg("Policy");
    public static override verboseNamePlural = msg("Policies");

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated policy.")
            : msg("Successfully created policy.");
    }
}
