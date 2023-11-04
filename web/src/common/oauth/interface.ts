import { state } from "@goauthentik/app/common/oauth/constants";
import { settings } from "@goauthentik/app/common/oauth/settings";
import { Interface } from "@goauthentik/app/elements/Base";
import { UserManager } from "oidc-client-ts";

export class OAuthInterface extends Interface {
    private async ensureLoggedIn() {
        const client = new UserManager(settings);
        const user = await client.getUser();
        if (user !== null) {
            return;
        }
        if (window.location.href.startsWith(settings.redirect_uri)) {
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
