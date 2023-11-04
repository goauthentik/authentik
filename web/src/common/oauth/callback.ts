import { state } from "@goauthentik/app/common/oauth/constants";
import { settings } from "@goauthentik/app/common/oauth/settings";
import { refreshMe } from "@goauthentik/app/common/users";
import { User, UserManager } from "oidc-client-ts";

import { LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-oauth-callback")
export class OAuthCallback extends LitElement {
    @property()
    params?: string;
    async firstUpdated(): Promise<void> {
        const client = new UserManager(settings);
        const user = (await client.signinCallback(`#${this.params}`)) as User;
        const st = user.state as state;
        window.location.assign(st.url);
        refreshMe();
    }
}
