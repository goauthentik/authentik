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

function coerceStoredAccount(value: unknown): BrowserLocalAccount | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const account = value as Partial<BrowserLocalAccount>;
    if (typeof account.uid !== "string" || !account.uid) {
        return null;
    }
    return {
        uid: account.uid,
        username: typeof account.username === "string" ? account.username : "",
        name: typeof account.name === "string" ? account.name : "",
        email: typeof account.email === "string" ? account.email : "",
        avatar: typeof account.avatar === "string" ? account.avatar : "",
        isCurrent: Boolean(account.isCurrent),
    };
}

export function readStoredAccounts(): BrowserLocalAccount[] {
    try {
        const stored = JSON.parse(localStorage.getItem(ACCOUNT_STORAGE_KEY) ?? "{}");
        if (!Array.isArray(stored.accounts)) {
            return [];
        }
        return stored.accounts
            .map((account: unknown) => coerceStoredAccount(account))
            .filter((account: BrowserLocalAccount | null): account is BrowserLocalAccount =>
                Boolean(account),
            );
    } catch {
        return [];
    }
}

export function writeStoredAccounts(accounts: BrowserLocalAccount[]): void {
    localStorage.setItem(ACCOUNT_STORAGE_KEY, JSON.stringify({ accounts }));
}

export function accountFromUser(user: UserSelf): BrowserLocalAccount {
    return {
        uid: user.uid,
        username: user.username,
        name: user.name,
        email: user.email ?? "",
        avatar: user.avatar ?? "",
        isCurrent: true,
    };
}
