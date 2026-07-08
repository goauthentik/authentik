import { StorageAccessor } from "#common/storage";

import type { UserSelf } from "@goauthentik/api";

const USER_STORAGE_KEY = "authentik.users";
// Keep this in sync with authentik/core/user_switching.py.
const USER_SWITCHING_COOKIE_NAME = "authentik_user_switching";

export interface BrowserLocalUser {
    pk: number;
    username: string;
    name: string;
    email: string;
    avatar: string;
    isCurrent: boolean;
}

interface StoredUsersPayload {
    users?: unknown;
}

const stringOrEmpty = (value: unknown): string => (typeof value === "string" ? value : "");

function userStorage(): StorageAccessor {
    return StorageAccessor.local(USER_STORAGE_KEY);
}

function readCookie(name: string): string | null {
    const prefix = `${name}=`;
    const cookie = document.cookie
        .split(";")
        .map((part) => part.trim())
        .find((part) => part.startsWith(prefix));
    return cookie ? decodeURIComponent(cookie.substring(prefix.length)) : null;
}

export function hasUserSwitchingToken(): boolean {
    return Boolean(readCookie(USER_SWITCHING_COOKIE_NAME));
}

export function coerceStoredUser(value: unknown): BrowserLocalUser | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const user = value as Partial<BrowserLocalUser>;
    if (typeof user.pk !== "number") {
        return null;
    }
    return {
        pk: user.pk,
        username: stringOrEmpty(user.username),
        name: stringOrEmpty(user.name),
        email: stringOrEmpty(user.email),
        avatar: stringOrEmpty(user.avatar),
        isCurrent: Boolean(user.isCurrent),
    };
}

export function coerceStoredUsers(value: unknown): BrowserLocalUser[] {
    if (!value || typeof value !== "object") {
        return [];
    }

    const { users } = value as StoredUsersPayload;
    if (!Array.isArray(users)) {
        return [];
    }

    return users
        .map((user: unknown) => coerceStoredUser(user))
        .filter((user: BrowserLocalUser | null): user is BrowserLocalUser => Boolean(user));
}

export function readStoredUsers(): BrowserLocalUser[] {
    return coerceStoredUsers(userStorage().readJSON<StoredUsersPayload>());
}

export function writeStoredUsers(users: BrowserLocalUser[]): boolean {
    return userStorage().writeJSON({ users });
}

export function removeStoredUser(pk: string): BrowserLocalUser[] {
    const users = readStoredUsers().filter((user) => user.pk.toString() !== pk);
    writeStoredUsers(users);
    return users;
}

function localUserFromUser(user: Readonly<UserSelf>): BrowserLocalUser {
    return {
        pk: user.pk,
        username: user.username,
        name: user.name,
        email: user.email ?? "",
        avatar: user.avatar ?? "",
        isCurrent: true,
    };
}

function userMatches(
    user: BrowserLocalUser,
    knownPKs: ReadonlySet<number>,
    knownUsernames: ReadonlySet<string>,
): boolean {
    return knownPKs.has(user.pk) || (user.username !== "" && knownUsernames.has(user.username));
}

export function mergeStoredUsers(
    currentLocalUser: BrowserLocalUser,
    storedUsers: readonly BrowserLocalUser[],
): BrowserLocalUser[] {
    const users = [currentLocalUser];
    const knownPKs = new Set([currentLocalUser.pk]);
    const knownUsernames = new Set(currentLocalUser.username ? [currentLocalUser.username] : []);

    for (const user of storedUsers) {
        if (userMatches(user, knownPKs, knownUsernames)) {
            continue;
        }
        users.push({ ...user, isCurrent: false });
        knownPKs.add(user.pk);
        if (user.username) {
            knownUsernames.add(user.username);
        }
    }

    return users;
}

/** Persist the current user into the deduped local user list. */
export function syncStoredUsers(user: Readonly<UserSelf> | null): BrowserLocalUser[] {
    if (!hasUserSwitchingToken()) {
        writeStoredUsers([]);
        return [];
    }

    if (!user) {
        return readStoredUsers();
    }
    const users = mergeStoredUsers(localUserFromUser(user), readStoredUsers());
    writeStoredUsers(users);
    return users;
}
