import { t } from "@lingui/macro";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { OutpostsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import "../../elements/Spinner";
import AKGlobal from "../../authentik.css";
import { PFColor } from "../../elements/Label";

@customElement("ak-outpost-health")
export class OutpostHealth extends LitElement {

    @property()
    outpostId?: string;

    static get styles(): CSSResult[] {
        return [PFBase, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.outpostId) {
            return html`<ak-spinner></ak-spinner>`;
        }
        return html`<ul>${until(new OutpostsApi(DEFAULT_CONFIG).outpostsOutpostsHealth({
            uuid: this.outpostId
        }).then((oh) => {
            if (oh.length === 0) {
                return html`<li>
                    <ul>
                        <li role="cell">
                            <ak-label color=${PFColor.Grey} text=${t`Not available`}></ak-label>
                        </li>
                    </ul>
                </li>`;
            }
            return oh.map((h) => {
                return html`<li>
                    <ul>
                        <li role="cell">
                            <ak-label color=${PFColor.Green} text=${t`Last seen: ${h.lastSeen?.toLocaleTimeString()}`}></ak-label>
                        </li>
                        <li role="cell">
                            ${h.versionOutdated ?
                            html`<ak-label color=${PFColor.Red}
                                text=${t`${h.version}, should be ${h.versionShould}`}></ak-label>` :
                            html`<ak-label color=${PFColor.Green} text=${t`Version: ${h.version || ""}`}></ak-label>`}
                        </li>
                    </ul>
                </li>`;
            });
        }), html`<ak-spinner></ak-spinner>`)}</ul>`;
    }

}
