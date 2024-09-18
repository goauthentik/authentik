import "@goauthentik/components/ak-text-input";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { ProxyProvider } from "@goauthentik/api";

import { ApplicationWizardProxyProviderForm } from "./ApplicationWizardProxyProviderForm.js";

@customElement("ak-application-wizard-provider-for-single-forward-proxy")
export class ApplicationWizardProviderSingleProxyForm extends ApplicationWizardProxyProviderForm {
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

    renderProxyMode(provider: ProxyProvider) {
        return html`<ak-text-input
            name="externalHost"
            value=${ifDefined(provider.externalHost)}
            required
            label=${msg("External host")}
            .errorMessages=${this.errorMessages("externalHost")}
            help=${msg(
                "The external URL you'll access the application at. Include any non-standard port.",
            )}
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-single-forward-proxy": ApplicationWizardProviderSingleProxyForm;
    }
}
