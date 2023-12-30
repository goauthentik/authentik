import { MemoryStore } from "@goauthentik/app/common/oauth/storage";
import { Log, OidcClientSettings, UserManagerSettings } from "oidc-client-ts";

Log.setLogger(console);
Log.setLevel(Log.DEBUG);

export const userSettings: OidcClientSettings & UserManagerSettings = {
    authority: `${window.location.origin}/application/o/authentik-user-interface/`,
    redirect_uri: `${window.location.origin}/if/user/#/oauth-callback/`,
    client_id: "authentik-user-interface",
    scope: "openid profile email goauthentik.io/api",
    response_mode: "fragment",
    automaticSilentRenew: true,
    userStore: new MemoryStore(),
};

export const adminSettings: OidcClientSettings & UserManagerSettings = {
    authority: `${window.location.origin}/application/o/authentik-admin-interface/`,
    redirect_uri: `${window.location.origin}/if/admin/#/oauth-callback/`,
    client_id: "authentik-admin-interface",
    scope: "openid profile email goauthentik.io/api",
    response_mode: "fragment",
    automaticSilentRenew: true,
    userStore: new MemoryStore(),
};
