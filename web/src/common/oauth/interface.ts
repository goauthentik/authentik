import { state } from "@goauthentik/common/oauth/constants";
import { settings } from "@goauthentik/common/oauth/settings";
import { AbstractConstructor } from "@goauthentik/elements/types";
import { UserManager } from "oidc-client-ts";

import type { LitElement } from "lit";

export function WithOAuth<T extends AbstractConstructor<LitElement>>(superclass: T) {
    abstract class OAuthInterface extends superclass {
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

    return OAuthInterface;
}
