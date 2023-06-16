import "@goauthentik/admin/applications/wizard/InitialApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/TypeApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/ldap/TypeLDAPApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/link/TypeLinkApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/oauth/TypeOAuthAPIApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/oauth/TypeOAuthApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/oauth/TypeOAuthCodeApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/oauth/TypeOAuthImplicitApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/proxy/TypeProxyApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/saml/TypeSAMLApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/saml/TypeSAMLConfigApplicationWizardPage";
import "@goauthentik/admin/applications/wizard/saml/TypeSAMLImportApplicationWizardPage";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/wizard/Wizard";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-application-wizard")
export class ApplicationWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
    }

    @property({ type: Boolean })
    open = false;

    @property()
    createText = msg("Create");

    @property({ type: Boolean })
    showButton = true;

    @property({ attribute: false })
    finalHandler: () => Promise<void> = () => {
        return Promise.resolve();
    };

    render(): TemplateResult {
        return html`
            <ak-wizard
                .open=${this.open}
                .steps=${["ak-application-wizard-initial", "ak-application-wizard-type"]}
                header=${msg("New application")}
                description=${msg("Create a new application.")}
                .finalHandler=${() => {
                    return this.finalHandler();
                }}
            >
                ${this.showButton
                    ? html`<button slot="trigger" class="pf-c-button pf-m-primary">
                          ${this.createText}
                      </button>`
                    : html``}
            </ak-wizard>
        `;
    }
}
