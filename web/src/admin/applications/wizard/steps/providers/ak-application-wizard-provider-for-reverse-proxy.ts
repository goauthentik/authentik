import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { ProxyProvider } from "@goauthentik/api";

import { ApplicationWizardProxyProviderForm } from "./ApplicationWizardProxyProviderForm.js";

@customElement("ak-application-wizard-provider-for-reverse-proxy")
export class ApplicationWizardProviderReverseProxyForm extends ApplicationWizardProxyProviderForm {
    renderModeDescription() {
        return html`<p class="pf-u-mb-xl">
            ${msg(
                "This provider will behave like a transparent reverse-proxy, except requests must be authenticated. If your upstream application uses HTTPS, make sure to connect to the outpost using HTTPS as well.",
            )}
        </p>`;
    }

    renderProxyMode(provider: ProxyProvider) {
        return html` <ak-text-input
                name="externalHost"
                value=${ifDefined(provider?.externalHost)}
                required
                label=${msg("External host")}
                .errorMessages=${this.errorMessages("externalHost")}
                help=${msg(
                    "The external URL you'll access the application at. Include any non-standard port.",
                )}
            ></ak-text-input>
            <ak-text-input
                name="internalHost"
                value=${ifDefined(provider?.internalHost)}
                .errorMessages=${this.errorMessages("internalHost")}
                required
                label=${msg("Internal host")}
                help=${msg("Upstream host that the requests are forwarded to.")}
            ></ak-text-input>
            <ak-switch-input
                name="internalHostSslValidation"
                ?checked=${provider?.internalHostSslValidation ?? true}
                label=${msg("Internal host SSL Validation")}
                help=${msg("Validate SSL Certificates of upstream servers.")}
            >
            </ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-reverse-proxy": ApplicationWizardProviderReverseProxyForm;
    }
}
