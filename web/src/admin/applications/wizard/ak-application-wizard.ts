import "#components/ak-wizard/ak-wizard-steps";
import "#admin/applications/wizard/steps/ak-application-wizard-application-step";
import "#admin/applications/wizard/steps/ak-application-wizard-bindings-step";
import "#admin/applications/wizard/steps/ak-application-wizard-edit-binding-step";
import "#admin/applications/wizard/steps/ak-application-wizard-provider-choice-step";
import "#admin/applications/wizard/steps/ak-application-wizard-provider-step";
import "#admin/applications/wizard/steps/ak-application-wizard-submit-step";

import { DEFAULT_CONFIG } from "#common/api/config";
import { assertEveryPresent } from "#common/utils";

import { listen } from "#elements/decorators/listen";
import { CreateWizard } from "#elements/wizard/CreateWizard";

import { WizardUpdateEvent } from "#components/ak-wizard/events";

import { applicationWizardProvidersContext } from "#admin/applications/wizard/ContextIdentity";
import {
    type ApplicationWizardContext,
    type ApplicationWizardContextUpdate,
} from "#admin/applications/wizard/steps/providers/shared";

import type { TypeCreate } from "@goauthentik/api";
import { ProviderModelEnum, ProvidersApi, ProxyMode } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";
import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

const createWizardContextValue = (): ApplicationWizardContext => ({
    providerModel: "",
    currentBinding: -1,
    app: {},
    provider: {},
    proxyMode: ProxyMode.Proxy,
    bindings: [],
    errors: {},
});

type ExtractProviderName<T extends string> = T extends `${string}.${infer Name}` ? Name : never;

type ProviderModelNameEnum = ExtractProviderName<ProviderModelEnum> | "samlproviderimportmodel";

export const providerTypePriority: ProviderModelNameEnum[] = [
    "oauth2provider",
    "samlprovider",
    "samlproviderimportmodel",
    "racprovider",
    "proxyprovider",
    "radiusprovider",
    "ldapprovider",
    "scimprovider",
    "wsfederationprovider",
];

@customElement("ak-application-wizard")
export class AKApplicationWizard extends CreateWizard {
    #api = new ProvidersApi(DEFAULT_CONFIG);

    public static override verboseName = msg("Application");
    public static override verboseNamePlural = msg("Applications");

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    @state()
    protected context: ApplicationWizardContext = createWizardContextValue();

    protected wizardProviderProvider = new ContextProvider(this, {
        context: applicationWizardProvidersContext,
        initialValue: [],
    });

    public override refresh = (): Promise<void> => {
        return this.#api.providersAllTypesList().then((providerTypes) => {
            const providerNameToProviderMap = new Map(
                providerTypes.map((providerType) => [providerType.modelName, providerType]),
            );

            const providersInOrder = providerTypePriority.map((name) =>
                providerNameToProviderMap.get(name),
            );

            assertEveryPresent<TypeCreate>(
                providersInOrder,
                "Provider priority list includes name for which no provider model was returned.",
            );

            this.wizardProviderProvider.setValue(providersInOrder);
        });
    };

    // This is the actual top of the Wizard; so this is where we accept the update information and
    // incorporate it into the wizard.
    /**
     * Handles updates to the wizard context, which are emitted by the individual steps when their data changes.
     */
    @listen(WizardUpdateEvent)
    handleUpdate(ev: WizardUpdateEvent<ApplicationWizardContextUpdate>) {
        ev.stopPropagation();
        const update = ev.content;

        if (update) {
            this.context = {
                ...this.context,
                ...update,
            };
        }
    }

    protected override render() {
        return html`<ak-wizard-steps>
            <ak-application-wizard-application-step
                slot="application"
                .wizard=${this.context}
            ></ak-application-wizard-application-step>
            <ak-application-wizard-provider-choice-step
                slot="provider-choice"
                .wizard=${this.context}
            ></ak-application-wizard-provider-choice-step>
            <ak-application-wizard-provider-step
                slot="provider"
                .wizard=${this.context}
            ></ak-application-wizard-provider-step>
            <ak-application-wizard-bindings-step
                slot="bindings"
                .wizard=${this.context}
            ></ak-application-wizard-bindings-step>
            <ak-application-wizard-edit-binding-step
                slot="edit-binding"
                .wizard=${this.context}
            ></ak-application-wizard-edit-binding-step>
            <ak-application-wizard-submit-step
                slot="submit"
                .wizard=${this.context}
            ></ak-application-wizard-submit-step>
        </ak-wizard-steps>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard": AKApplicationWizard;
    }
}
