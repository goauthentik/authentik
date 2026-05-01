import { ModelForm } from "#elements/forms/ModelForm";

import type { Stage } from "@goauthentik/api/dist/models/Stage";

import { msg } from "@lit/localize";

export abstract class BaseStageForm<T extends Stage> extends ModelForm<T, string> {
    public static override verboseName = msg("Stage");
    public static override verboseNamePlural = msg("Stages");

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated stage.")
            : msg("Successfully created stage.");
    }
}
