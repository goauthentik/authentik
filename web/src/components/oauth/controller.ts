import { state } from "@goauthentik/components/oauth/constants";
import { Interface } from "@goauthentik/elements/Interface/index.js";
import { UserManager, UserManagerSettings } from "oidc-client-ts";

import { ReactiveController, ReactiveControllerHost } from "lit";

type ReactiveInterfaceHost = Partial<ReactiveControllerHost> & Interface;

export class OAuthLoginController implements ReactiveController {
    checked = false;

    constructor(
        private host: ReactiveInterfaceHost,
        private settings: UserManagerSettings
    ) {
        this.host.addController(this);
    }

    hostUpdated() {
        if (this.checked) {
            return;
        }
        this.checked = true;
        this.ensureLoggedIn();
    }

    private async ensureLoggedIn() {
        const client = new UserManager(this.settings);
        const user = await client.getUser();
        if (user !== null) {
            return;
        }
        if (window.location.href.startsWith(this.settings.redirect_uri)) {
            return;
        }
        const s = new state();
        await client.signinRedirect({
            state: s,
        });
    }
}
