import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TypeCreate } from "@goauthentik/api";

import { WizardPage } from "../../../elements/wizard/WizardPage";

@customElement("ak-application-wizard-type")
export class TypeApplicationWizardPage extends WizardPage {
    applicationTypes: TypeCreate[] = [
        {
            component: "ak-application-wizard-type-oauth",
            name: t`OAuth2/OIDC`,
            description: t`Modern applications, APIs and Single-page applications.`,
            modelName: "",
        },
        {
            component: "ak-application-wizard-type-saml",
            name: t`SAML`,
            description: t`XML-based SSO standard. Use this if your application only supports SAML.`,
            modelName: "",
        },
        {
            component: "ak-application-wizard-type-proxy",
            name: t`Proxy`,
            description: t`Legacy applications which don't natively support SSO.`,
            modelName: "",
        },
        {
            component: "ak-application-wizard-type-ldap",
            name: t`LDAP`,
            description: t`Provide an LDAP interface for applications and users to authenticate against.`,
            modelName: "",
        },
        {
            component: "ak-application-wizard-type-link",
            name: t`Link`,
            description: t`Provide an LDAP interface for applications and users to authenticate against.`,
            modelName: "",
        },
    ];

    sidebarLabel = () => t`Authentication method`;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFForm, PFRadio, AKGlobal];
    }

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.applicationTypes.map((type) => {
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${type.component}
                        @change=${() => {
                            this.host.steps = [
                                "ak-application-wizard-initial",
                                "ak-application-wizard-type",
                                type.component,
                            ];
                            this.host.isValid = true;
                        }}
                    />
                    <label class="pf-c-radio__label" for=${type.component}>${type.name}</label>
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        </form>`;
    }
}
