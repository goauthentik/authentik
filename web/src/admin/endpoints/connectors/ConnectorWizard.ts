import "#elements/LicenseNotice";
import "#admin/endpoints/connectors/agent/AgentConnectorForm";
import "#admin/endpoints/connectors/fleet/FleetConnectorForm";
import "#admin/endpoints/connectors/gdtc/GoogleChromeConnectorForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { aki } from "#common/api/client";

import { SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { EndpointsApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

@customElement("ak-endpoint-connector-wizard")
export class AKEndpointConnectorWizard extends CreateWizard {
    #api = aki(EndpointsApi);

    public static override verboseName = msg("Endpoint Connector");
    public static override verboseNamePlural = msg("Endpoint Connectors");

    public override layout = TypeCreateWizardPageLayouts.grid;

    protected apiEndpoint = (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.#api.endpointsConnectorsTypesList(requestInit);
    };

    protected override renderInitialPageContent(): SlottedTemplateResult {
        return msg(
            "Connectors are required to create devices. Depending on connector type, agents either directly talk to them or they talk to and external API to create devices.",
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoint-connector-wizard": AKEndpointConnectorWizard;
    }
}
