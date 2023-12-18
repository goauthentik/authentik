import { state } from "@goauthentik/app/common/oauth/constants";
import { Interface } from "@goauthentik/app/elements/Base";
import { UserManager, UserManagerSettings } from "oidc-client-ts";

export abstract class OAuthInterface extends Interface {
    abstract get oauthSettings(): UserManagerSettings;

    private async ensureLoggedIn() {
        const client = new UserManager(this.oauthSettings);
        const user = await client.getUser();
        if (user !== null) {
            return;
        }
        if (window.location.href.startsWith(this.oauthSettings.redirect_uri)) {
            return;
        }
        const s = new state();
        await client.signinRedirect({
            state: s,
        });
    }

    async firstUpdated(_changedProperties: Map<PropertyKey, unknown>): Promise<void> {
        await this.ensureLoggedIn();
        await super.firstUpdated(_changedProperties);
    }
}
