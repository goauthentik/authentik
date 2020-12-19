import { DefaultClient } from "./Client";

interface TokenResponse {
    key: string;
}

export function tokenByIdentifier(identifier: string): Promise<string> {
    return DefaultClient.fetch<TokenResponse>(["core", "tokens", identifier, "view_key"]).then(
        (r) => r.key
    );
}
