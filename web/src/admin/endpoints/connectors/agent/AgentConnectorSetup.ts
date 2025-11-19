import { AKElement } from "#elements/Base";

import { AgentConnector } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-endpoints-connector-agent-setup")
export class AgentConnectorSetup extends AKElement {
    @property({ attribute: false })
    connector?: AgentConnector;

    static styles: CSSResult[] = [PFBase, PFList];

    render() {
        return html`<p>${msg("Download the latest package from here:")}</p>
            <ul class="pf-c-list pf-m-inline">
                <li>
                    <a
                        href="https://pkg.goauthentik.io/packages/authentik_windows-2025_agent/agent_local/agent.msi"
                        >${msg("Windows")}</a
                    >
                </li>
                <li>
                    <a
                        href="https://pkg.goauthentik.io/packages/authentik_macos-15_agent/agent_local/authentik%20agent%20installer.pkg"
                        >${msg("macOS")}</a
                    >
                </li>
                <li><a href="https://pkg.goauthentik.io/">${msg("Linux")}</a></li>
            </ul>
            <p>${msg("Afterwards, download the configuration for your MDM Software")}</p> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent-setup": AgentConnectorSetup;
    }
}
