import "#components/ak-wizard/ak-wizard-steps";
import "./steps/ak-application-wizard-application-step.js";
import "./steps/ak-application-wizard-bindings-step.js";
import "./steps/ak-application-wizard-edit-binding-step.js";
import "./steps/ak-application-wizard-provider-choice-step.js";
import "./steps/ak-application-wizard-provider-step.js";
import "./steps/ak-application-wizard-submit-step.js";

import { applicationWizardProvidersContext } from "./ContextIdentity.js";
import { type ApplicationWizardState, type ApplicationWizardStateUpdate } from "./types.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { WizardUpdateEvent } from "#components/ak-wizard/events";

import type { TypeCreate } from "@goauthentik/api";
import { ProvidersApi, ProxyMode } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

const freshWizardState = (): ApplicationWizardState => ({
    providerModel: "",
    currentBinding: -1,
    app: {},
    provider: {},
    proxyMode: ProxyMode.Proxy,
    bindings: [],
    errors: {},
});

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isTypeCreateArray = (v: any): v is TypeCreate[] => Array.isArray(v) && !v.includes(undefined);

export const providerTypePriority = [
    "oauth2provider",
    "samlprovider",
    "samlproviderimportmodel",
    "racprovider",
    "proxyprovider",
    "radiusprovider",
    "ldapprovider",
    "scimprovider",
];

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
            const providerNameToProviderMap = new Map(
                providerTypes.map((providerType) => [providerType.modelName, providerType]),
            );
            const providersInOrder = providerTypePriority.map((name) =>
                providerNameToProviderMap.get(name),
            );
            if (!isTypeCreateArray(providersInOrder)) {
                throw new Error(
                    "Provider priority list includes name for which no provider model was returned.",
                );
            }
            this.wizardProviderProvider.setValue(providersInOrder);
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
