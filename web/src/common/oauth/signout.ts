import { settings } from "@goauthentik/app/common/oauth/settings";
import { UserManager } from "oidc-client-ts";

import { LitElement } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-oauth-signout")
export class OAuthSignout extends LitElement {
    async firstUpdated(): Promise<void> {
        const client = new UserManager(settings);
        await client.signoutRedirect();
    }
}
