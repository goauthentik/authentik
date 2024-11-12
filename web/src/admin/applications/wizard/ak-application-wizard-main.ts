import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-wizard/ak-wizard-steps.js";
import { WizardUpdateEvent } from "@goauthentik/components/ak-wizard/events";
import { AKElement } from "@goauthentik/elements/Base.js";

import { ContextProvider } from "@lit/context";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { ProvidersApi, ProxyMode } from "@goauthentik/api";

import { applicationWizardProvidersContext } from "./ContextIdentity";
import { providerTypeRenderers } from "./steps/ProviderChoices.js";
import "./steps/ak-application-wizard-application-step.js";
import "./steps/ak-application-wizard-bindings-step.js";
import "./steps/ak-application-wizard-edit-binding-step.js";
import "./steps/ak-application-wizard-provider-choice-step.js";
import "./steps/ak-application-wizard-provider-step.js";
import "./steps/ak-application-wizard-submit-step.js";
import { type ApplicationWizardState, type ApplicationWizardStateUpdate } from "./types";

const freshWizardState = (): ApplicationWizardState => ({
    providerModel: "",
    currentBinding: -1,
    app: {},
    provider: {},
    proxyMode: ProxyMode.Proxy,
    bindings: [],
    errors: {},
});

@customElement("ak-application-wizard-main")
export class AkApplicationWizardMain extends AKElement {
    @state()
    wizard: ApplicationWizardState = freshWizardState();

    wizardProviderProvider = new ContextProvider(this, {
        context: applicationWizardProvidersContext,
        initialValue: [],
    });

    constructor() {
        super();
        this.addEventListener(WizardUpdateEvent.eventName, this.handleUpdate);
    }

    connectedCallback() {
        super.connectedCallback();
        new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList().then((providerTypes) => {
            const wizardReadyProviders = Object.keys(providerTypeRenderers);
            this.wizardProviderProvider.setValue(
                providerTypes
                    .filter((providerType) => wizardReadyProviders.includes(providerType.modelName))
                    .map((providerType) => ({
                        ...providerType,
                        renderer: providerTypeRenderers[providerType.modelName].render,
                    }))
                    .sort(
                        (a, b) =>
                            providerTypeRenderers[a.modelName].order -
                            providerTypeRenderers[b.modelName].order,
                    )
                    .reverse(),
            );
        });
    }

    // This is the actual top of the Wizard; so this is where we accept the update information and
    // incorporate it into the wizard.
    handleUpdate(ev: WizardUpdateEvent<ApplicationWizardStateUpdate>) {
        ev.stopPropagation();
        const update = ev.content;
        if (update !== undefined) {
            this.wizard = {
                ...this.wizard,
                ...update,
            };
        }
    }

    render() {
        return html`<ak-wizard-steps>
            <ak-application-wizard-application-step
                slot="application"
                .wizard=${this.wizard}
            ></ak-application-wizard-application-step>
            <ak-application-wizard-provider-choice-step
                slot="provider-choice"
                .wizard=${this.wizard}
            ></ak-application-wizard-provider-choice-step>
            <ak-application-wizard-provider-step
                slot="provider"
                .wizard=${this.wizard}
            ></ak-application-wizard-provider-step>
            <ak-application-wizard-bindings-step
                slot="bindings"
                .wizard=${this.wizard}
            ></ak-application-wizard-bindings-step>
            <ak-application-wizard-edit-binding-step
                slot="edit-binding"
                .wizard=${this.wizard}
            ></ak-application-wizard-edit-binding-step>
            <ak-application-wizard-submit-step
                slot="submit"
                .wizard=${this.wizard}
            ></ak-application-wizard-submit-step>
        </ak-wizard-steps>`;
    }
}
