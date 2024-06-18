import { UserManager, UserManagerSettings } from "oidc-client-ts";

import { LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-oauth-signout")
export class OAuthSignout extends LitElement {
    @property({ attribute: false })
    settings?: UserManagerSettings;
    async firstUpdated(): Promise<void> {
        if (!this.settings) {
            return;
        }
        const client = new UserManager(this.settings);
        await client.signoutRedirect();
    }
}
