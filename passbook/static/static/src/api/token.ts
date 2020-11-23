export function tokenByIdentifier(identifier: string): Promise<string> {
    return fetch(`/api/v2beta/core/tokens/${identifier}/view_key/`)
        .then((r) => r.json())
        .then((r) => r["key"]);
}
