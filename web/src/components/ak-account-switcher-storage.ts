import { StorageAccessor } from "#common/storage";

import type { UserSelf } from "@goauthentik/api";

const ACCOUNT_STORAGE_KEY = "authentik.accounts";
const USER_SWITCHING_STORAGE_KEY = "authentik.user_switching";
const USER_SWITCHING_COOKIE_NAME = "authentik_user_switching";
const USER_SWITCHING_COOKIE_AGE_SECONDS = 60 * 60 * 24 * 365;

export interface BrowserLocalAccount {
    pk: number;
    username: string;
    name: string;
    email: string;
    avatar: string;
    isCurrent: boolean;
}

interface StoredAccountsPayload {
    accounts?: unknown;
}

const stringOrEmpty = (value: unknown): string => (typeof value === "string" ? value : "");

function accountStorage(): StorageAccessor {
    return StorageAccessor.local(ACCOUNT_STORAGE_KEY);
}

function userSwitchingStorage(): StorageAccessor {
    return StorageAccessor.local(USER_SWITCHING_STORAGE_KEY);
}

function readCookie(name: string): string | null {
    const prefix = `${name}=`;
    const cookie = document.cookie
        .split(";")
        .map((part) => part.trim())
        .find((part) => part.startsWith(prefix));
    return cookie ? decodeURIComponent(cookie.substring(prefix.length)) : null;
}

function writeUserSwitchingCookie(value: string): void {
    const secure = window.location.protocol === "https:";
    document.cookie = [
        `${USER_SWITCHING_COOKIE_NAME}=${encodeURIComponent(value)}`,
        `Max-Age=${USER_SWITCHING_COOKIE_AGE_SECONDS}`,
        "Path=/",
        `SameSite=${secure ? "None" : "Lax"}`,
        secure ? "Secure" : "",
    ]
        .filter(Boolean)
        .join("; ");
}

export function syncUserSwitchingToken(): string | null {
    const token = readCookie(USER_SWITCHING_COOKIE_NAME);
    if (token) {
        userSwitchingStorage().write(token);
        return token;
    }

    const stored = userSwitchingStorage().read<string>();
    if (stored) {
        writeUserSwitchingCookie(stored);
    }
    return stored;
}

export function coerceStoredAccount(value: unknown): BrowserLocalAccount | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const account = value as Partial<BrowserLocalAccount>;
    if (typeof account.pk !== "number") {
        return null;
    }
    return {
        pk: account.pk,
        username: stringOrEmpty(account.username),
        name: stringOrEmpty(account.name),
        email: stringOrEmpty(account.email),
        avatar: stringOrEmpty(account.avatar),
        isCurrent: Boolean(account.isCurrent),
    };
}

export function coerceStoredAccounts(value: unknown): BrowserLocalAccount[] {
    if (!value || typeof value !== "object") {
        return [];
    }

    const { accounts } = value as StoredAccountsPayload;
    if (!Array.isArray(accounts)) {
        return [];
    }

    return accounts
        .map((account: unknown) => coerceStoredAccount(account))
        .filter((account: BrowserLocalAccount | null): account is BrowserLocalAccount =>
            Boolean(account),
        );
}

export function readStoredAccounts(): BrowserLocalAccount[] {
    return coerceStoredAccounts(accountStorage().readJSON<StoredAccountsPayload>());
}

export function writeStoredAccounts(accounts: BrowserLocalAccount[]): boolean {
    return accountStorage().writeJSON({ accounts });
}

export function removeStoredAccount(pk: string): BrowserLocalAccount[] {
    const accounts = readStoredAccounts().filter((account) => account.pk.toString() !== pk);
    writeStoredAccounts(accounts);
    return accounts;
}

function accountFromUser(user: Readonly<UserSelf>): BrowserLocalAccount {
    return {
        pk: user.pk,
        username: user.username,
        name: user.name,
        email: user.email ?? "",
        avatar: user.avatar ?? "",
        isCurrent: true,
    };
}

function accountMatches(
    account: BrowserLocalAccount,
    knownPKs: ReadonlySet<number>,
    knownUsernames: ReadonlySet<string>,
): boolean {
    return (
        knownPKs.has(account.pk) ||
        (account.username !== "" && knownUsernames.has(account.username))
    );
}

export function mergeStoredAccounts(
    currentAccount: BrowserLocalAccount,
    storedAccounts: readonly BrowserLocalAccount[],
): BrowserLocalAccount[] {
    const accounts = [currentAccount];
    const knownPKs = new Set([currentAccount.pk]);
    const knownUsernames = new Set(currentAccount.username ? [currentAccount.username] : []);

    for (const account of storedAccounts) {
        if (accountMatches(account, knownPKs, knownUsernames)) {
            continue;
        }
        accounts.push({ ...account, isCurrent: false });
        knownPKs.add(account.pk);
        if (account.username) {
            knownUsernames.add(account.username);
        }
    }

    return accounts;
}

/** Persist the current user into the deduped local account list. */
export function syncStoredAccounts(user: Readonly<UserSelf> | null): BrowserLocalAccount[] {
    syncUserSwitchingToken();

    if (!user) {
        return readStoredAccounts();
    }

    const accounts = mergeStoredAccounts(accountFromUser(user), readStoredAccounts());
    writeStoredAccounts(accounts);
    return accounts;
}
