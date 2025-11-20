import { EntityLabel } from "#common/i18n/nouns";
import { ActionTenseRecord } from "#common/i18n/verbs";

import { msg, str } from "@lit/localize";

/**
 * Formats a success message for an action performed on an entity.
 *
 * @param pastTenseVerb The past tense of the action verb.
 * @param singularNoun The singular form of the entity noun.
 * @returns A formatted success message.
 *
 * @see {@linkcode formatSuccessMessage} for a wrapper around this function.
 */
export function formatSuccessActionMessage(pastTenseVerb: string, singularNoun: string): string {
    return msg(str`Successfully ${pastTenseVerb} ${singularNoun}.`, {
        id: "success-action-message",
        desc: "A message indicating that an action was successfully performed on an entity, with placeholders for the verb and noun",
    });
}

/**
 * Formats a success message for creating or updating an entity.
 *
 * @param singularNoun The singular form of the entity noun.
 * @param instance If truthy, indicates an update action; otherwise, a create action.
 * @returns A formatted success message.
 *
 * @see {@linkcode formatSuccessActionMessage} for the underlying formatting logic.
 */
export function formatSuccessMessage(singularNoun: string, instance: unknown = false): string {
    return instance
        ? formatSuccessActionMessage(ActionTenseRecord.update.past().toLowerCase(), singularNoun)
        : formatSuccessActionMessage(ActionTenseRecord.create.past().toLowerCase(), singularNoun);
}

/**
 * Formats an error message for an action that failed to be performed on an entity.
 *
 * @param presentTenseVerb The present tense of the action verb.
 * @param singularNoun The singular form of the entity noun.
 * @returns A formatted error message.
 *
 * @see {@linkcode formatErrorMessage} for a wrapper around this function.
 */
export function formatErrorActionMessage(presentTenseVerb: string, singularNoun: string): string {
    return msg(str`Failed to ${presentTenseVerb} ${singularNoun}.`, {
        id: "error-action-message",
        desc: "A message indicating that an action failed to be performed on an entity, with placeholders for the verb and noun",
    });
}

/**
 * Formats an error message for creating or updating an entity.
 *
 * @param singularNoun The singular form of the entity noun.
 * @param instance If truthy, indicates an update action; otherwise, a create action.
 * @returns A formatted error message.
 *
 * @see {@linkcode formatErrorActionMessage} for the underlying formatting logic.
 */
export function formatErrorMessage(singularNoun: string, instance: unknown = false): string {
    return instance
        ? formatErrorActionMessage(ActionTenseRecord.update.present().toLowerCase(), singularNoun)
        : formatErrorActionMessage(ActionTenseRecord.create.present().toLowerCase(), singularNoun);
}

/**
 * Label for opening a "new entity" modal or page.
 */
export function formatNewMessage(label: EntityLabel | string): string {
    const singular = typeof label === "string" ? label : label.singular;

    return msg(str`New ${singular}`, {
        id: "new-entity-label",
        desc: "Label for opening a new entity modal or page",
    });
}

/**
 * Label for a "create entity" button.
 */
export function formatCreateMessage(label: EntityLabel | string): string {
    const singular = typeof label === "string" ? label : label.singular;

    return msg(str`${ActionTenseRecord.create.present()} ${singular}`, {
        id: "create-entity-button-label",
        desc: "Label for a button that creates a new entity",
    });
}

/**
 * Label for an "edit entity" button.
 */
export function formatEditMessage(label: EntityLabel | string): string {
    const singular = typeof label === "string" ? label : label.singular;

    return msg(str`${ActionTenseRecord.edit.present()} ${singular}`, {
        id: "edit-entity-button-label",
        desc: "Label for a button that edits an existing entity",
    });
}
