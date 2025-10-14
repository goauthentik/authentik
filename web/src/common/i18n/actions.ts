import { EntityLabel } from "#common/i18n/nouns";
import { ActionTenseRecord } from "#common/i18n/verbs";

import { msg, str } from "@lit/localize";

export function formatSuccessActionMessage(pastTenseVerb: string, singularNoun: string): string {
    return msg(`Successfully ${pastTenseVerb} ${singularNoun}.`);
}

export function formatSuccessMessage(singularNoun: string, instance: unknown = false): string {
    return instance
        ? formatSuccessActionMessage(ActionTenseRecord.update.past.toLowerCase(), singularNoun)
        : formatSuccessActionMessage(ActionTenseRecord.create.past.toLowerCase(), singularNoun);
}

export function formatErrorActionMessage(presentTenseVerb: string, singularNoun: string): string {
    return msg(`Successfully ${presentTenseVerb} ${singularNoun}.`);
}

export function formatFailureMessage(singularNoun: string, instance: unknown = false): string {
    return instance
        ? formatSuccessActionMessage(ActionTenseRecord.update.past.toLowerCase(), singularNoun)
        : formatSuccessActionMessage(ActionTenseRecord.create.past.toLowerCase(), singularNoun);
}

/**
 * Label for opening a "new entity" modal or page.
 */
export function formatNewMessage(label: EntityLabel | string): string {
    const singular = typeof label === "string" ? label : label.singular;

    return msg(str`New ${singular}`);
}

/**
 * Label for a "create entity" button.
 */
export function formatCreateMessage(label: EntityLabel | string): string {
    const singular = typeof label === "string" ? label : label.singular;

    return msg(str`${ActionTenseRecord.create.present} ${singular}`);
}

/**
 * Label for an "edit entity" button.
 */
export function formatEditMessage(label: EntityLabel | string): string {
    const singular = typeof label === "string" ? label : label.singular;

    return msg(str`${ActionTenseRecord.edit.present} ${singular}`);
}
