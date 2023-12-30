import { state } from "@goauthentik/app/common/oauth/constants";
import { refreshMe } from "@goauthentik/app/common/users";
import { User, UserManager, UserManagerSettings } from "oidc-client-ts";

import { LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-oauth-callback")
export class OAuthCallback extends LitElement {
    @property()
    params?: string;
    @property({ attribute: false })
    settings?: UserManagerSettings;
    async firstUpdated(): Promise<void> {
        if (!this.settings) {
            return;
        }
        const client = new UserManager(this.settings);
        const user = (await client.signinCallback(`#${this.params}`)) as User;
        const st = user.state as state;
        window.location.assign(st.url);
        refreshMe();
    }
}
