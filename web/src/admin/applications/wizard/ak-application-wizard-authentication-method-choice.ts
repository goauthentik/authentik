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

// The provider description that comes from the server is fairly specific and not internationalized.
// We provide alternative descriptions that use the phrase 'authentication method' instead, and make
// it available to i18n.
//
// prettier-ignore
const alternativeDescription = new Map<string, string>([
    ["oauth2provider", msg("Modern applications, APIs and Single-page applications.")],
    ["samlprovider", msg("XML-based SSO standard. Use this if your application only supports SAML.")],
    ["proxyprovider", msg("Legacy applications which don't natively support SSO.")],
    ["ldapprovider", msg("Provide an LDAP interface for applications and users to authenticate against.")]
]);

@customElement("ak-application-wizard-authentication-method-choice")
export class ApplicationWizardAuthenticationMethodChoice extends ApplicationWizardPageBase {
    @state()
    providerTypes: TypeCreate[] = [];

    constructor() {
        super();
        this.handleChoice = this.handleChoice.bind(this);
        this.renderProvider = this.renderProvider.bind(this);
        // If the provider doesn't supply a model to which to send our initialization, the user will
        // have to use the older provider path.
        new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList().then((types) => {
            this.providerTypes = types.filter(({ modelName }) => modelName.trim() !== "");
        });
    }

    handleChoice(ev: InputEvent) {
        const target = ev.target as HTMLInputElement;

        this.dispatchWizardUpdate({ providerType: target.value });
    }

    renderProvider(type: TypeCreate) {
        const description = alternativeDescription.has(type.modelName)
            ? alternativeDescription.get(type.modelName)
            : type.description;

        const label = type.name.replace(/\s+Provider/, "");

        return html`<div class="pf-c-radio">
            <input
                class="pf-c-radio__input"
                type="radio"
                name="type"
                id=${type.component}
                value=${type.modelName}
                @change=${this.handleChoice}
            />
            <label class="pf-c-radio__label" for=${type.component}>${label}</label>
            <span class="pf-c-radio__description">${description}</span>
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
