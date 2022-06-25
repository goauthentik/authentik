import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../../../elements/wizard/Wizard";
import "./InitialApplicationWizardPage";
import "./TypeApplicationWizardPage";
import "./ldap/TypeLDAPApplicationWizardPage";
import "./link/TypeLinkApplicationWizardPage";
import "./oauth/TypeOAuthAPIApplicationWizardPage";
import "./oauth/TypeOAuthApplicationWizardPage";
import "./oauth/TypeOAuthCodeApplicationWizardPage";
import "./oauth/TypeOAuthImplicitApplicationWizardPage";
import "./proxy/TypeProxyApplicationWizardPage";
import "./saml/TypeSAMLApplicationWizardPage";
import "./saml/TypeSAMLConfigApplicationWizardPage";
import "./saml/TypeSAMLImportApplicationWizardPage";

@customElement("ak-application-wizard")
export class ApplicationWizard extends LitElement {
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
