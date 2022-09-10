import { PFColor } from "@goauthentik/web/elements/Label";
import "@goauthentik/web/elements/Spinner";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostHealth } from "@goauthentik/api";

@customElement("ak-outpost-health")
export class OutpostHealthElement extends LitElement {
    @property({ attribute: false })
    outpostHealth?: OutpostHealth;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            AKGlobal,
            css`
                li {
                    margin: 5px 0;
                }
            `,
        ];
    }

    render(): TemplateResult {
        if (!this.outpostHealth) {
            return html`<ak-spinner></ak-spinner>`;
        }
        let versionString = this.outpostHealth.version;
        if (this.outpostHealth.buildHash) {
            versionString = `${versionString} (build ${this.outpostHealth.buildHash.substring(
                0,
                8,
            )})`;
        }
        return html` <ul>
            <li>
                <ak-label color=${PFColor.Green}>
                    ${t`Last seen: ${this.outpostHealth.lastSeen?.toLocaleTimeString()}`}
                </ak-label>
            </li>
            <li>
                ${this.outpostHealth.versionOutdated
                    ? html`<ak-label color=${PFColor.Red}
                          >${t`${this.outpostHealth.version}, should be ${this.outpostHealth.versionShould}`}
                      </ak-label>`
                    : html`<ak-label color=${PFColor.Green}
                          >${t`Version: ${versionString}`}
                      </ak-label>`}
            </li>
        </ul>`;
    }
}
