export interface User {
    pk: number;
    username: string;
    name: string;
    is_superuser: boolean;
    email: boolean;
    avatar: string;
}

export function me(): Promise<User> {
    return fetch("/api/v2beta/core/users/me/")
        .then((r) => r.json())
        .then((r) => <User>r);
}
