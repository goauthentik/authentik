import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";

export abstract class BasePolicyForm<T> extends ModelForm<T, string> {
    protected override entityLabel = msg("policy");
}
