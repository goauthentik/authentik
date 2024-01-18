import { first } from "@goauthentik/common/utils.js";
import "@goauthentik/components/ak-switch-input.js";
import "@goauthentik/components/ak-text-input.js";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { ProxyProvider } from "@goauthentik/api";

import AkTypeProxyApplicationWizardPage from "./AuthenticationByProxyPage";

@customElement("ak-application-wizard-authentication-for-reverse-proxy")
export class AkReverseProxyApplicationWizardPage extends AkTypeProxyApplicationWizardPage {
    renderModeDescription() {
        return html`<p class="pf-u-mb-xl">
            ${msg(
                "This provider will behave like a transparent reverse-proxy, except requests must be authenticated. If your upstream application uses HTTPS, make sure to connect to the outpost using HTTPS as well.",
            )}
        </p>`;
    }

    renderProxyMode() {
        const provider = this.wizard.provider as ProxyProvider | undefined;
        const errors = this.wizard.errors.provider;

        return html` <ak-text-input
                name="externalHost"
                value=${ifDefined(provider?.externalHost)}
                required
                label=${msg("External host")}
                .errorMessages=${errors?.externalHost ?? []}
                help=${msg(
                    "The external URL you'll access the application at. Include any non-standard port.",
                )}
            ></ak-text-input>
            <ak-text-input
                name="internalHost"
                value=${ifDefined(provider?.internalHost)}
                .errorMessages=${errors?.internalHost ?? []}
                required
                label=${msg("Internal host")}
                help=${msg("Upstream host that the requests are forwarded to.")}
            ></ak-text-input>
            <ak-switch-input
                name="internalHostSslValidation"
                ?checked=${first(provider?.internalHostSslValidation, true)}
                label=${msg("Internal host SSL Validation")}
                help=${msg("Validate SSL Certificates of upstream servers.")}
            >
            </ak-switch-input>`;
    }
}

export default AkReverseProxyApplicationWizardPage;
