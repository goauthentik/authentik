import "#admin/outposts/ServiceConnectionDockerForm";
import "#admin/outposts/ServiceConnectionKubernetesForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CreateWizard } from "#elements/wizard/CreateWizard";

import { OutpostsApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize/init/install";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

@customElement("ak-service-connection-wizard")
export class AKServiceConnectionWizard extends CreateWizard {
    public static override verboseName = msg("Outpost Integration");
    public static override verboseNamePlural = msg("Outpost Integrations");

    #api = new OutpostsApi(DEFAULT_CONFIG);

    protected apiEndpoint = (): Promise<TypeCreate[]> => {
        return this.#api.outpostsServiceConnectionsAllTypesList();
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-service-connection-wizard": AKServiceConnectionWizard;
    }
}
