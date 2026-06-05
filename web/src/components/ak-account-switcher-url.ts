export interface AccountSelectionURLUser {
    email?: string;
    uid?: string;
    username?: string;
}

export interface AuthenticationFlowURLConfig {
    account?: AccountSelectionURLUser;
    accountSelectionFlow?: string | null;
    apiBase: string;
    next: string;
}

export function buildAuthenticationFlowURL({
    account,
    accountSelectionFlow,
    apiBase,
    next,
}: AuthenticationFlowURLConfig): string {
    const query = new URLSearchParams({ next });
    const loginHint = account?.email || account?.username;

    if (account?.uid && accountSelectionFlow) {
        query.set("account_uid", account.uid);
        return `${apiBase}if/flow/${accountSelectionFlow}/?${query.toString()}`;
    }

    if (!account?.uid) {
        query.set("add_account", "true");
    }

    if (loginHint) {
        query.set("login_hint", loginHint);
    }

    return `${apiBase}flows/-/default/authentication/?${query.toString()}`;
}
