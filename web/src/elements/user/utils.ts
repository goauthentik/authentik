import { DEFAULT_CONFIG } from "#common/api/config";

import { DeleteForm } from "#elements/forms/DeleteForm";

import { CoreApi, User } from "@goauthentik/api";

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

/**
 * Get the list of objects that depend on a user.
 * Used for delete confirmation dialogs.
 */
export function userUsedBy(user: User) {
    return new CoreApi(DEFAULT_CONFIG).coreUsersUsedByList({
        id: user.pk,
    });
}

/**
 * Delete a user via the API.
 */
export function deleteUser(user: User) {
    return new CoreApi(DEFAULT_CONFIG).coreUsersDestroy({
        id: user.pk,
    });
}
