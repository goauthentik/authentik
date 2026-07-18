import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BaseSourceForm<T extends object = object> extends ModelForm<T, string> {
    public static override verboseName = msg("Source");
    public static override verboseNamePlural = msg("Sources");
    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated source.")
            : msg("Successfully created source.");
    }
}
