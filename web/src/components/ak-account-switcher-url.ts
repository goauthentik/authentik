export interface UserSelectionURLUser {
    email?: string;
    uid?: string;
    username?: string;
}

export interface AuthenticationFlowURLConfig {
    account?: UserSelectionURLUser;
    userSelectionFlow?: string | null;
    apiBase: string;
    next: string;
}

export function buildAuthenticationFlowURL({
    account,
    userSelectionFlow,
    apiBase,
    next,
}: AuthenticationFlowURLConfig): string {
    const query = new URLSearchParams({ next });
    const loginHint = account?.email || account?.username;

    if (account?.uid && userSelectionFlow) {
        query.set("user_uid", account.uid);
        return `${apiBase}if/flow/${userSelectionFlow}/?${query.toString()}`;
    }

    if (!account?.uid) {
        query.delete("user_uid");
    }

    if (loginHint) {
        query.set("login_hint", loginHint);
    }

    return `${apiBase}flows/-/default/authentication/?${query.toString()}`;
}
