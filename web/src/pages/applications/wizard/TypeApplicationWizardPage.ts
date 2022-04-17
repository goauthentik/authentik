import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TypeCreate } from "@goauthentik/api";

import { WizardPage } from "../../../elements/wizard/WizardPage";

@customElement("ak-application-wizard-type")
export class TypeApplicationWizardPage extends WizardPage {
    @property({ attribute: false })
    applicationTypes: TypeCreate[] = [
        {
            component: "",
            name: "OAuth2/OIDC",
            description: t`Modern applications, APIs and Single-page=applications.`,
            modelName: "",
        },
        {
            component: "",
            name: "SAML",
            description: "XML-based SSO standard. Use this if your application only supports SAML.",
            modelName: "",
        },
        {
            component: "proxy",
            name: "Proxy",
            description: t`Legacy applications which don't natively support SSO.`,
            modelName: "",
        },
        {
            component: "",
            name: "LDAP",
            description: t`Provide an LDAP interface for applications and users to authenticate against.`,
            modelName: "",
        },
    ];

    sidebarLabel = () => t`Protocol details`;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    render(): TemplateResult {
        return html`
            ${this.applicationTypes.map((type) => {
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${type.component}
                        @change=${() => {
                            this.host.setSteps("initial", "type", `type-${type.component}`);
                            this._isValid = true;
                        }}
                    />
                    <label class="pf-c-radio__label" for=${type.component}>${type.name}</label>
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        `;
    }
}
