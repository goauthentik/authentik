export interface UserSelectionURLUser {
    email?: string;
    uid?: string;
    username?: string;
}

export interface AuthenticationFlowURLConfig {
    apiBase: string;
    next: string;
}

export interface AccountSwitchFlowURLConfig extends AuthenticationFlowURLConfig {
    account: UserSelectionURLUser;
    userSelectionFlow?: string | null;
}

export function buildAccountSwitchFlowURL({
    account,
    userSelectionFlow,
    apiBase,
    next,
}: AccountSwitchFlowURLConfig): string | null {
    if (!account.uid) {
        return null;
    }
    const query = new URLSearchParams({
        next,
        user_uid: account.uid,
    });
    if (!userSelectionFlow) {
        return `${apiBase}flows/-/default/user-selection/?${query.toString()}`;
    }
    return `${apiBase}if/flow/${userSelectionFlow}/?${query.toString()}`;
}

export function buildAuthenticationFlowURL({ apiBase, next }: AuthenticationFlowURLConfig): string {
    const query = new URLSearchParams({ next });
    return `${apiBase}flows/-/default/authentication/?${query.toString()}`;
}
