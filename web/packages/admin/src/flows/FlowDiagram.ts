import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { Diagram } from "@goauthentik/elements/Diagram.js";
import "@goauthentik/elements/EmptyState.js";

import { customElement, property } from "lit/decorators.js";

import { FlowsApi } from "@goauthentik/api";

@customElement("ak-flow-diagram")
export class FlowDiagram extends Diagram {
    @property()
    flowSlug?: string;

    refreshHandler = (): void => {
        this.diagram = undefined;
        new FlowsApi(DEFAULT_CONFIG)
            .flowsInstancesDiagramRetrieve({
                slug: this.flowSlug || "",
            })
            .then((data) => {
                this.diagram = data.diagram;
                this.requestUpdate();
            });
    };
}
