import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { map } from "lit/directives/map.js";

import type { TypeCreate } from "@goauthentik/api";

import BasePanel from "../BasePanel";
import providerTypesList from "./ak-application-wizard-authentication-method-choice.choices";

@customElement("ak-application-wizard-authentication-method-choice")
export class ApplicationWizardAuthenticationMethodChoice extends BasePanel {
    constructor() {
        super();
        this.handleChoice = this.handleChoice.bind(this);
        this.renderProvider = this.renderProvider.bind(this);
    }

    handleChoice(ev: InputEvent) {
        const target = ev.target as HTMLInputElement;
        this.dispatchWizardUpdate({ providerType: target.value });
    }

    renderProvider(type: TypeCreate) {
        const method = this.wizard.providerType;

        return html`<div class="pf-c-radio">
            <input
                class="pf-c-radio__input"
                type="radio"
                name="type"
                id="provider-${type.modelName}"
                value=${type.modelName}
                ?checked=${type.modelName === method}
                @change=${this.handleChoice}
            />
            <label class="pf-c-radio__label" for="provider-${type.modelName}">${type.name}</label>
            <span class="pf-c-radio__description">${type.description}</span>
        </div>`;
    }

    render() {
        return providerTypesList.length > 0
            ? html`<form class="pf-c-form pf-m-horizontal">
                  ${map(providerTypesList, this.renderProvider)}
              </form>`
            : html`<ak-empty-state loading header=${msg("Loading")}></ak-empty-state>`;
    }
}

export default ApplicationWizardAuthenticationMethodChoice;
