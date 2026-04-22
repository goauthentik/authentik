import { DEFAULT_CONFIG } from "#common/api/config";
import { isResponseErrorLike } from "#common/errors/network";
import { UIConfig, UserDisplay } from "#common/ui/config";

import { CoreApi, SessionUser, UserSelf } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";

export interface ClientSessionPermissions {
    editApplications: boolean;
    accessAdmin: boolean;
}

export type UserLike = Partial<Pick<UserSelf, "username" | "name" | "email">>;

/**
 * The display name of the current user, according to their UI config settings.
 */
export function formatUserDisplayName(user: UserLike | null, uiConfig?: UIConfig): string {
    if (!user) return "";

    const label = match(uiConfig?.navbar.userDisplay)
        .with(UserDisplay.username, () => user.username)
        .with(UserDisplay.name, () => user.name)
        .with(UserDisplay.email, () => user.email)
        .with(UserDisplay.none, () => null)
        .otherwise(() => user.name || user.username);

    return label || "";
}

const formatUnknownUserLabel = () =>
    msg("Unknown user", {
        id: "user.display.unknownUser",
        desc: "Placeholder for an unknown user, in the format 'Unknown user'.",
    });

/**
 * Format a user's display name with disambiguation, such as when multiple users have the same name appearing in a list.
 */
export function formatDisambiguatedUserDisplayName(
    user?: UserLike | null,
    formatter?: Intl.ListFormat,
): string;
export function formatDisambiguatedUserDisplayName(
    user?: UserLike | null,
    locale?: Intl.LocalesArgument,
): string;
export function formatDisambiguatedUserDisplayName(
    user?: UserLike | null,
    localeOrFormatter?: Intl.ListFormat | Intl.LocalesArgument,
): string {
    if (!user) {
        return formatUnknownUserLabel();
    }

    const formatter =
        localeOrFormatter instanceof Intl.ListFormat
            ? localeOrFormatter
            : new Intl.ListFormat(localeOrFormatter, { style: "narrow", type: "unit" });

    const { username, name, email } = user;

    const segments: string[] = [];

    if (username) {
        segments.push(username);
    }

    if (name && name !== username) {
        if (segments.length === 0) {
            segments.push(name);
        } else {
            segments.push(
                msg(str`(${name})`, {
                    id: "user.display.nameInParens",
                    desc: "The user's name in parentheses, used when the name is different from the username",
                }),
            );
        }
    }
    if (email && email !== username) {
        segments.push(
            msg(str`<${email}>`, {
                id: "user.display.emailInAngleBrackets",
                desc: "The user's email in angle brackets, used when the email is different from the username",
            }),
        );
    }

    if (!segments.length) {
        return formatUnknownUserLabel();
    }

    return formatter.format(segments);
}

/**
 * Whether the current session is an unauthenticated guest session.
 */
export function isGuest(user: UserSelf | null): boolean {
    return user?.pk === -1;
}

/**
 * Create a guest session for unauthenticated users.
 *
 * @see {@linkcode me} for the actual session retrieval.
 */
function createGuestSession(): SessionUser {
    const guest: SessionUser = {
        user: {
            pk: -1,
            isSuperuser: false,
            isActive: true,
            groups: [],
            roles: [],
            avatar: "",
            uid: "",
            username: "",
            name: "",
            settings: {},
            systemPermissions: [],
        },
    };

    return guest;
}

let pendingRedirect = false;

/**
 * Redirect to the default authentication flow, preserving the current URL as "next" parameter.
 *
 * @category Session
 */
export function redirectToAuthFlow(nextPathname = "/flows/-/default/authentication/"): void {
    if (pendingRedirect) {
        console.debug("authentik/users: Redirect already pending, ");
        return;
    }

    const { pathname, search, hash } = window.location;

    const authFlowRedirectURL = new URL(nextPathname, window.location.origin);

    authFlowRedirectURL.searchParams.set("next", `${pathname}${search}${hash}`);

    pendingRedirect = true;

    console.debug(
        `authentik/users: Redirecting to authentication flow at ${authFlowRedirectURL.href}`,
    );

    window.location.assign(authFlowRedirectURL);
}

/**
 * Retrieve the current user session.
 *
 * This is a memoized function, so it will only make one request per page load.
 *
 * @see {@linkcode refreshMe} to force a refresh.
 *
 * @category Session
 */
export async function me(requestInit?: RequestInit): Promise<SessionUser> {
    return new CoreApi(DEFAULT_CONFIG)
        .coreUsersMeRetrieve(requestInit)
        .catch(async (error: unknown) => {
            if (isResponseErrorLike(error)) {
                const { response } = error;

                if (response.status === 401 || response.status === 403) {
                    redirectToAuthFlow();
                }
            }

            console.debug("authentik/users: Failed to retrieve user session", error);

            return createGuestSession();
        });
}
