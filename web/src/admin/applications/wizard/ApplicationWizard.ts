import "@goauthentik/web/admin/applications/wizard/InitialApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/TypeApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/ldap/TypeLDAPApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/link/TypeLinkApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/oauth/TypeOAuthAPIApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/oauth/TypeOAuthApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/oauth/TypeOAuthCodeApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/oauth/TypeOAuthImplicitApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/proxy/TypeProxyApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/saml/TypeSAMLApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/saml/TypeSAMLConfigApplicationWizardPage";
import "@goauthentik/web/admin/applications/wizard/saml/TypeSAMLImportApplicationWizardPage";
import { AKElement } from "@goauthentik/web/elements/Base";
import "@goauthentik/web/elements/wizard/Wizard";

import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/common/styles/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-application-wizard")
export class ApplicationWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property({ type: Boolean })
    open = false;

    @property()
    createText = t`Create`;

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
                header=${t`New application`}
                description=${t`Create a new application.`}
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
