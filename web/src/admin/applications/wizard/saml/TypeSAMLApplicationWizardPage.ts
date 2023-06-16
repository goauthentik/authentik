import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TypeCreate } from "@goauthentik/api";

@customElement("ak-application-wizard-type-saml")
export class TypeOAuthApplicationWizardPage extends WizardPage {
    applicationTypes: TypeCreate[] = [
        {
            component: "ak-application-wizard-type-saml-import",
            name: msg("Import SAML Metadata"),
            description: msg(
                "Import the metadata document of the applicaation you want to configure.",
            ),
            modelName: "",
        },
        {
            component: "ak-application-wizard-type-saml-config",
            name: msg("Manual configuration"),
            description: msg("Manually configure SAML"),
            modelName: "",
        },
    ];

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFForm, PFRadio];
    }

    sidebarLabel = () => msg("Application type");

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
                                "ak-application-wizard-type-saml",
                                type.component,
                            ];
                            this.host.state["saml-type"] = type.component;
                            this.host.isValid = true;
                        }}
                    />
                    <label class="pf-c-radio__label" for=${type.component}>${type.name}</label>
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        </form> `;
    }
}
