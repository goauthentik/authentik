import "@goauthentik/components/ak-text-input";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import AkTypeProxyApplicationWizardPage from "./AuthenticationByProxyPage";

@customElement("ak-application-wizard-authentication-for-single-forward-proxy")
export class AkForwardSingleProxyApplicationWizardPage extends AkTypeProxyApplicationWizardPage {
    renderModeDescription() {
        return html`<p class="pf-u-mb-xl">
            ${msg(
                html`Use this provider with nginx's <code>auth_request</code> or traefik's
                    <code>forwardAuth</code>. Each application/domain needs its own provider.
                    Additionally, on each domain, <code>/outpost.goauthentik.io</code> must be
                    routed to the outpost (when using a managed outpost, this is done for you).`,
            )}
        </p>`;
    }

    renderProxyMode() {
        return html`<ak-text-input
            name="externalHost"
            value=${ifDefined(this.instance?.externalHost)}
            required
            label=${msg("External host")}
            help=${msg(
                "The external URL you'll access the application at. Include any non-standard port.",
            )}
        ></ak-text-input>`;
    }
}

export default AkForwardSingleProxyApplicationWizardPage;
