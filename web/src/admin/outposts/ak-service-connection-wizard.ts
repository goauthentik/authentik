import "#admin/outposts/ServiceConnectionDockerForm";
import "#admin/outposts/ServiceConnectionKubernetesForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";
import { aki } from "#common/api/client";

import { formatCreateLabel } from "#elements/dialogs/shared";
import { toAdminInterface } from "#elements/router/core/interfaces";
import { CreateWizard } from "#elements/wizard/CreateWizard";

import { AKFullPageWizard } from "#components/ak-wizard/ak-full-page-wizard";

import { OutpostsApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize/init/install";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

@customElement("ak-service-connection-wizard")
export class AKServiceConnectionWizard extends CreateWizard {
    public static override verboseName = msg("Outpost Integration");
    public static override verboseNamePlural = msg("Outpost Integrations");

    #api = aki(OutpostsApi);

    protected apiEndpoint = (): Promise<TypeCreate[]> => {
        return this.#api.outpostsServiceConnectionsAllTypesList();
    };
}

/**
 * The outpost integration wizard as a full page, for the `/outpost/integrations/new` route.
 */
@customElement("ak-service-connection-wizard-page")
export class AKServiceConnectionWizardPage extends AKFullPageWizard {
    public override header = formatCreateLabel(AKServiceConnectionWizard);
    public override icon = "pf-icon pf-icon-integration";
    public override returnURL = toAdminInterface("outpost/integrations");

    protected override render() {
        return html`<ak-service-connection-wizard></ak-service-connection-wizard>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-service-connection-wizard": AKServiceConnectionWizard;
        "ak-service-connection-wizard-page": AKServiceConnectionWizardPage;
    }
}
