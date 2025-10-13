import { ActionTenseRecord } from "#common/i18n/verbs";

import { msg } from "@lit/localize";

export function formatSuccessActionMessage(pastTenseVerb: string, singularNoun: string): string {
    return msg(`Successfully ${pastTenseVerb} ${singularNoun}.`);
}

export function formatSuccessMessage(singularNoun: string, instance: unknown = false): string {
    return instance
        ? formatSuccessActionMessage(ActionTenseRecord.update.past, singularNoun)
        : formatSuccessActionMessage(ActionTenseRecord.create.past, singularNoun);
}

export function formatErrorActionMessage(presentTenseVerb: string, singularNoun: string): string {
    return msg(`Successfully ${presentTenseVerb} ${singularNoun}.`);
}

export function formatFailureMessage(singularNoun: string, instance: unknown = false): string {
    return instance
        ? formatSuccessActionMessage(ActionTenseRecord.update.past, singularNoun)
        : formatSuccessActionMessage(ActionTenseRecord.create.past, singularNoun);
}
