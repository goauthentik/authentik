import "@goauthentik/components/ak-text-input";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import AkTypeProxyApplicationWizardPage from "./AuthenticationByProxyPage";

@customElement("ak-application-wizard-authentication-for-forward-proxy-domain")
export class AkForwardDomainProxyApplicationWizardPage extends AkTypeProxyApplicationWizardPage {
    renderModeDescription() {
        return html`<p class="pf-u-mb-xl">
                ${msg(
                    "Use this provider with nginx's auth_request or traefik's forwardAuth. Only a single provider is required per root domain. You can't do per-application authorization, but you don't have to create a provider for each application.",
                )}
            </p>
            <div class="pf-u-mb-xl">
                ${msg("An example setup can look like this:")}
                <ul class="pf-c-list">
                    <li>${msg("authentik running on auth.example.com")}</li>
                    <li>${msg("app1 running on app1.example.com")}</li>
                </ul>
                ${msg(
                    "In this case, you'd set the Authentication URL to auth.example.com and Cookie domain to example.com.",
                )}
            </div>`;
    }

    renderProxyMode() {
        return html`
            <ak-text-input
                name="externalHost"
                label=${msg("External host")}
                value=${ifDefined(this.instance?.externalHost)}
                required
                help=${msg(
                    "The external URL you'll authenticate at. The authentik core server should be reachable under this URL.",
                )}
            >
            </ak-text-input>
            <ak-text-input
                name="cookieDomain"
                label=${msg("Cookie domain")}
                value="${ifDefined(this.instance?.cookieDomain)}"
                required
                help=${msg(
                    "Set this to the domain you wish the authentication to be valid for. Must be a parent domain of the URL above. If you're running applications as app1.domain.tld, app2.domain.tld, set this to 'domain.tld'.",
                )}
            ></ak-text-input>
        `;
    }
}

export default AkForwardDomainProxyApplicationWizardPage;
