import { StorageAccessor } from "#common/storage";

import type { UserSelf } from "@goauthentik/api";

const ACCOUNT_STORAGE_KEY = "authentik.accounts";
const BROWSER_STORAGE_KEY = "authentik.browser";
const BROWSER_COOKIE_NAME = "authentik_browser";
const BROWSER_COOKIE_AGE_SECONDS = 60 * 60 * 24 * 365;

export interface BrowserLocalAccount {
    uid: string;
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

function browserStorage(): StorageAccessor {
    return StorageAccessor.local(BROWSER_STORAGE_KEY);
}

function readCookie(name: string): string | null {
    const prefix = `${name}=`;
    const cookie = document.cookie
        .split(";")
        .map((part) => part.trim())
        .find((part) => part.startsWith(prefix));
    return cookie ? decodeURIComponent(cookie.substring(prefix.length)) : null;
}

function writeBrowserCookie(value: string): void {
    const secure = window.location.protocol === "https:";
    document.cookie = [
        `${BROWSER_COOKIE_NAME}=${encodeURIComponent(value)}`,
        `Max-Age=${BROWSER_COOKIE_AGE_SECONDS}`,
        "Path=/",
        `SameSite=${secure ? "None" : "Lax"}`,
        secure ? "Secure" : "",
    ]
        .filter(Boolean)
        .join("; ");
}

export function syncBrowserToken(): string | null {
    const token = readCookie(BROWSER_COOKIE_NAME);
    if (token) {
        browserStorage().write(token);
        return token;
    }

    const stored = browserStorage().read<string>();
    if (stored) {
        writeBrowserCookie(stored);
    }
    return stored;
}

export function coerceStoredAccount(value: unknown): BrowserLocalAccount | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const account = value as Partial<BrowserLocalAccount>;
    if (typeof account.uid !== "string" || !account.uid) {
        return null;
    }
    return {
        uid: account.uid,
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

export function removeStoredAccount(uid: string): BrowserLocalAccount[] {
    const accounts = readStoredAccounts().filter((account) => account.uid !== uid);
    writeStoredAccounts(accounts);
    return accounts;
}

function accountFromUser(user: Readonly<UserSelf>): BrowserLocalAccount {
    return {
        uid: user.uid,
        username: user.username,
        name: user.name,
        email: user.email ?? "",
        avatar: user.avatar ?? "",
        isCurrent: true,
    };
}

function accountMatches(
    account: BrowserLocalAccount,
    knownUIDs: ReadonlySet<string>,
    knownUsernames: ReadonlySet<string>,
): boolean {
    return (
        knownUIDs.has(account.uid) ||
        (account.username !== "" && knownUsernames.has(account.username))
    );
}

export function mergeStoredAccounts(
    currentAccount: BrowserLocalAccount,
    storedAccounts: readonly BrowserLocalAccount[],
): BrowserLocalAccount[] {
    const accounts = [currentAccount];
    const knownUIDs = new Set([currentAccount.uid]);
    const knownUsernames = new Set(currentAccount.username ? [currentAccount.username] : []);

    for (const account of storedAccounts) {
        if (accountMatches(account, knownUIDs, knownUsernames)) {
            continue;
        }
        accounts.push({ ...account, isCurrent: false });
        knownUIDs.add(account.uid);
        if (account.username) {
            knownUsernames.add(account.username);
        }
    }

    return accounts;
}

/** Persist the current user into the deduped local account list. */
export function syncStoredAccounts(user: Readonly<UserSelf> | null): BrowserLocalAccount[] {
    syncBrowserToken();

    if (!user) {
        return readStoredAccounts();
    }

    const accounts = mergeStoredAccounts(accountFromUser(user), readStoredAccounts());
    writeStoredAccounts(accounts);
    return accounts;
}
