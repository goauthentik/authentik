import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { property } from "lit/decorators.js";

interface NamedPolicy {
    name: string;
}

export abstract class BasePolicyForm<T extends NamedPolicy> extends ModelForm<T, string> {
    public static override verboseName = msg("Policy");
    public static override verboseNamePlural = msg("Policies");

    @property({ type: Boolean })
    public copyMode = false;

    getSuccessMessage(): string {
        return this.instancePk
            ? msg("Successfully updated policy.")
            : msg("Successfully created policy.");
    }

    protected override assignInstance(instance: T | null): void {
        if (instance && this.copyMode) {
            this.instancePk = null;
            super.assignInstance({ ...instance, name: `${instance.name} - copy` });
            return;
        }
        super.assignInstance(instance);
    }
}
