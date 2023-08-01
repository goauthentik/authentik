import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { state } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import { ProvidersApi } from "@goauthentik/api";
import type { TypeCreate } from "@goauthentik/api";

import ApplicationWizardPageBase from "./ApplicationWizardPageBase";

@customElement("ak-application-wizard-authentication-method-choice")
export class ApplicationWizardAuthenticationMethodChoice extends ApplicationWizardPageBase {
    @state()
    providerTypes: TypeCreate[] = [];

    constructor() {
        super();
        this.handleChoice = this.handleChoice.bind(this);
        this.renderProvider = this.renderProvider.bind(this);
        new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList().then((types) => {
            this.providerTypes = types;
        });
    }

    handleChoice(ev: Event) {
        this.dispatchWizardUpdate({ providerType: ev.target.value });
    }

    renderProvider(type: Provider) {
        // Special case; the SAML-by-import method is handled differently
        // prettier-ignore
        const model = /^SAML/.test(type.name) && type.modelName === ""
            ? "samlimporter"
            : type.modelName;

        return html`<div class="pf-c-radio">
            <input
                class="pf-c-radio__input"
                type="radio"
                name="type"
                id=${type.component}
                value=${model}
                @change=${this.handleChoice}
            />
            <label class="pf-c-radio__label" for=${type.component}>${type.name}</label>
            <span class="pf-c-radio__description">${type.description}</span>
        </div>`;
    }

    render() {
        return this.providerTypes.length > 0
            ? html`<form class="pf-c-form pf-m-horizontal">
                  ${map(this.providerTypes, this.renderProvider)}
              </form>`
            : html`<ak-empty-state loading header=${msg("Loading")}></ak-empty-state>`;
    }
}

export default ApplicationWizardAuthenticationMethodChoice;
