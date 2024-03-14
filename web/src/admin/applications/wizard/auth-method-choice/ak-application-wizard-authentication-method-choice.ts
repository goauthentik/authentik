import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html, nothing } from "lit";
import { map } from "lit/directives/map.js";

import BasePanel from "../BasePanel";
import providerModelsList from "./ak-application-wizard-authentication-method-choice.choices";
import type { LocalTypeCreate } from "./ak-application-wizard-authentication-method-choice.choices";

@customElement("ak-application-wizard-authentication-method-choice")
export class ApplicationWizardAuthenticationMethodChoice extends WithLicenseSummary(BasePanel) {
    constructor() {
        super();
        this.handleChoice = this.handleChoice.bind(this);
        this.renderProvider = this.renderProvider.bind(this);
    }

    handleChoice(ev: InputEvent) {
        const target = ev.target as HTMLInputElement;
        this.dispatchWizardUpdate({
            update: {
                ...this.wizard,
                providerModel: target.value,
                errors: {},
            },
            status: this.valid ? "valid" : "invalid",
        });
    }

    renderProvider(type: LocalTypeCreate) {
        const method = this.wizard.providerModel;

        return html`<div class="pf-c-radio">
            <input
                class="pf-c-radio__input"
                type="radio"
                name="type"
                id="provider-${type.formName}"
                ?disabled=${type.formName === "racprovider" && !this.hasEnterpriseLicense}
                value=${type.formName}
                ?checked=${type.formName === method}
                @change=${this.handleChoice}
            />
            <label class="pf-c-radio__label" for="provider-${type.formName}">${type.name}</label>
            <span class="pf-c-radio__description"
                >${type.description}${type.note ? type.note() : nothing}</span
            >
        </div>`;
    }

    render() {
        return providerModelsList.length > 0
            ? html`<form class="pf-c-form pf-m-horizontal">
                  ${map(providerModelsList, this.renderProvider)}
              </form>`
            : html`<ak-empty-state loading header=${msg("Loading")}></ak-empty-state>`;
    }
}

export default ApplicationWizardAuthenticationMethodChoice;
