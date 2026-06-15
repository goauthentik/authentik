import { StorageAccessor } from "#common/storage";

import type { UserSelf } from "@goauthentik/api";

const ACCOUNT_STORAGE_KEY = "authentik.accounts";

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

/**
 * Merge the current user into the stored account list, persist it, and return it.
 *
 * Accounts are deduped by uid and by username (usernames are unique server-side),
 * so the same account never shows up twice regardless of what was stored.
 */
export function syncStoredAccounts(user: Readonly<UserSelf> | null): BrowserLocalAccount[] {
    if (!user) {
        return readStoredAccounts();
    }

    const accounts = mergeStoredAccounts(accountFromUser(user), readStoredAccounts());
    writeStoredAccounts(accounts);
    return accounts;
}
