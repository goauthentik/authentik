import "#elements/Spinner";

import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { OutpostHealth } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-outpost-health")
export class OutpostHealthElement extends AKElement {
    @property({ attribute: false })
    outpostHealth?: OutpostHealth;

    static styles: CSSResult[] = [
        PFDescriptionList,
        css`
            li {
                margin: 5px 0;
            }
        `,
    ];

    render(): TemplateResult {
        if (!this.outpostHealth) {
            return html`<ak-spinner></ak-spinner>`;
        }
        let versionString = this.outpostHealth.version;
        if (this.outpostHealth.buildHash) {
            versionString = msg(
                str`${versionString} (build ${this.outpostHealth.buildHash.substring(0, 8)})`,
            );
        }
        if (this.outpostHealth.fipsEnabled) {
            versionString = msg(str`${versionString} (FIPS)`);
        }
        return html`<dl class="pf-c-description-list pf-m-compact">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Last seen")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <ak-label color=${PFColor.Green} compact>
                            ${msg(
                                str`${formatElapsedTime(this.outpostHealth.lastSeen)} (${this.outpostHealth.lastSeen?.toLocaleTimeString()})`,
                            )}
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
                            ? html`<ak-label color=${PFColor.Red} compact
                                  >${msg(
                                      str`${this.outpostHealth.version}, should be ${this.outpostHealth.versionShould}`,
                                  )}
                              </ak-label>`
                            : html`<ak-label color=${PFColor.Green} compact
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-outpost-health": OutpostHealthElement;
    }
}
