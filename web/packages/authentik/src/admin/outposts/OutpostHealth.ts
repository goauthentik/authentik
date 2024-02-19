import { AKElement } from "@goauthentik/elements/Base";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/Spinner";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostHealth } from "@goauthentik/api";

@customElement("ak-outpost-health")
export class OutpostHealthElement extends AKElement {
    @property({ attribute: false })
    outpostHealth?: OutpostHealth;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFDescriptionList,
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
        return html`<dl class="pf-c-description-list pf-m-compact">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Last seen")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <ak-label color=${PFColor.Green} ?compact=${true}>
                            ${this.outpostHealth.lastSeen?.toLocaleTimeString()}
                        </ak-label>
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Version")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${this.outpostHealth.versionOutdated
                            ? html`<ak-label color=${PFColor.Red} ?compact=${true}
                                  >${msg(
                                      str`${this.outpostHealth.version}, should be ${this.outpostHealth.versionShould}`,
                                  )}
                              </ak-label>`
                            : html`<ak-label color=${PFColor.Green} ?compact=${true}
                                  >${versionString}
                              </ak-label>`}
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Hostname")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${this.outpostHealth.hostname}</div>
                </dd>
            </div>
        </dl> `;
    }
}
