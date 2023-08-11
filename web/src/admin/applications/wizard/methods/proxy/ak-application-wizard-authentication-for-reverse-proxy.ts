import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

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
        return html` <ak-text-input
                name="externalHost"
                value=${ifDefined(this.instance?.externalHost)}
                required
                label=${msg("External host")}
                help=${msg(
                    "The external URL you'll access the application at. Include any non-standard port.",
                )}
            ></ak-text-input>
            <ak-text-input
                name="internalHost"
                value=${ifDefined(this.instance?.internalHost)}
                required
                label=${msg("Internal host")}
                help=${msg("Upstream host that the requests are forwarded to.")}
            ></ak-text-input>
            <ak-switch-input
                name="internalHostSslValidation"
                ?checked=${first(this.instance?.internalHostSslValidation, true)}
                label=${msg("Internal host SSL Validation")}
                help=${msg("Validate SSL Certificates of upstream servers.")}
            >
            </ak-switch-input>`;
    }
}

export default AkReverseProxyApplicationWizardPage;
