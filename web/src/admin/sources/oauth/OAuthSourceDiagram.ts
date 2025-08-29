import { Diagram } from "#elements/Diagram";

import { UserMatchingModeToLabel } from "#admin/sources/oauth/utils";

import { OAuthSource, UserMatchingModeEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-oauth-diagram")
export class OAuthSourceDiagram extends Diagram {
    @property({ attribute: false })
    source?: OAuthSource;

    refreshHandler = (): void => {
        if (!this.source) return;
        const graph = ["graph LR"];
        graph.push(`source[${msg(str`OAuth Source ${this.source.name}`)}]`);
        graph.push(
            `source --> flow_manager["${UserMatchingModeToLabel(
                this.source.userMatchingMode || UserMatchingModeEnum.Identifier,
            )}"]`,
        );
        if (this.source.enrollmentFlow) {
            graph.push("flow_manager --> flow_enroll[Enrollment flow]");
        }
        if (this.source.authenticationFlow) {
            graph.push("flow_manager --> flow_auth[Authentication flow]");
        }
        this.diagram = graph.join("\n");
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-oauth-diagram": OAuthSourceDiagram;
    }
}
