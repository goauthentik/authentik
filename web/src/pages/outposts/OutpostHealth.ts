import { t } from "@lingui/macro";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { OutpostHealth, OutpostsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import "../../elements/Spinner";
import AKGlobal from "../../authentik.css";
import { PFColor } from "../../elements/Label";
import { EVENT_REFRESH } from "../../constants";

@customElement("ak-outpost-health")
export class OutpostHealthElement extends LitElement {
    @property()
    outpostId?: string;

    @property({ attribute: false })
    outpostHealth?: OutpostHealth[];

    @property({ attribute: false })
    showVersion = true;

    static get styles(): CSSResult[] {
        return [PFBase, AKGlobal];
    }

    constructor() {
        super();
        window.addEventListener(EVENT_REFRESH, () => {
            this.outpostHealth = undefined;
            this.firstUpdated();
        });
    }

    firstUpdated(): void {
        if (!this.outpostId) return;
        new OutpostsApi(DEFAULT_CONFIG)
            .outpostsInstancesHealthList({
                uuid: this.outpostId,
            })
            .then((health) => {
                this.outpostHealth = health;
            });
    }

    render(): TemplateResult {
        if (!this.outpostId || !this.outpostHealth) {
            return html`<ak-spinner></ak-spinner>`;
        }
        if (this.outpostHealth.length === 0) {
            return html` <ul>
                <li role="cell">
                    <ak-label color=${PFColor.Grey} text=${t`Not available`}></ak-label>
                </li>
            </ul>`;
        }
        return html`<ul>
            ${this.outpostHealth.map((h) => {
                return html`<li>
                    <ul>
                        <li role="cell">
                            <ak-label
                                color=${PFColor.Green}
                                text=${t`Last seen: ${h.lastSeen?.toLocaleTimeString()}`}
                            ></ak-label>
                        </li>
                        ${this.showVersion
                            ? html`<li role="cell">
                                  ${h.versionOutdated
                                      ? html`<ak-label
                                            color=${PFColor.Red}
                                            text=${t`${h.version}, should be ${h.versionShould}`}
                                        ></ak-label>`
                                      : html`<ak-label
                                            color=${PFColor.Green}
                                            text=${t`Version: ${h.version || ""}`}
                                        ></ak-label>`}
                              </li>`
                            : html``}
                    </ul>
                </li>`;
            })}
        </ul>`;
    }
}
