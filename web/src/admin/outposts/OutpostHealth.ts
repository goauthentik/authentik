import { AKElement } from "@goauthentik/elements/Base";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/Spinner";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostHealth } from "@goauthentik/api";

@customElement("ak-outpost-health")
export class OutpostHealthElement extends AKElement {
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
                    ${msg(str`Last seen: ${this.outpostHealth.lastSeen?.toLocaleTimeString()}`)}
                </ak-label>
            </li>
            <li>
                ${this.outpostHealth.versionOutdated
                    ? html`<ak-label color=${PFColor.Red}
                          >${msg(
                              str`${this.outpostHealth.version}, should be ${this.outpostHealth.versionShould}`,
                          )}
                      </ak-label>`
                    : html`<ak-label color=${PFColor.Green}
                          >${msg(str`Version: ${versionString}`)}
                      </ak-label>`}
            </li>
        </ul>`;
    }
}
