import { ModelForm } from "#elements/forms/ModelForm";

<<<<<<< HEAD
=======
import type { Stage } from "@goauthentik/api";

>>>>>>> 1db6c3af8 (web: Fix Vendored Lex package. Add Unit Tests  (#22083))
import { msg } from "@lit/localize";

export abstract class BaseStageForm<T extends object> extends ModelForm<T, string> {
    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated stage.")
            : msg("Successfully created stage.");
    }
}
