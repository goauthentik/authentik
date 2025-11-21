import { DeleteForm } from "#elements/forms/DeleteForm";

import { User } from "@goauthentik/api";

export function UserOption(user: User): string {
    let finalString = user.username;
    if (user.name || user.email) {
        finalString += " (";
        if (user.name) {
            finalString += user.name;
            if (user.email) {
                finalString += ", ";
            }
        }
        if (user.email) {
            finalString += user.email;
        }
        finalString += ")";
    }
    return finalString;
}

/**
 * Get a display-friendly name for a user object.
 * Falls back to username if no display name (name field) is set.
 *
 * @param user - The user object
 * @returns The user's display name or username
 */
export function getUserDisplayName(user: User): string {
    return user.name || user.username;
}

/**
 * Base class for delete/update forms that work with User objects.
 * Automatically uses username as fallback when user has no display name.
 */
export class UserDeleteForm extends DeleteForm {
    protected override getObjectDisplayName(): string | undefined {
        return this.obj ? getUserDisplayName(this.obj as unknown as User) : undefined;
    }
}
