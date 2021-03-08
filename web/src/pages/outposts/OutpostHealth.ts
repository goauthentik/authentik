import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { OutpostsApi } from "../../api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { COMMON_STYLES } from "../../common/styles";
import "../../elements/Spinner";

@customElement("ak-outpost-health")
export class OutpostHealth extends LitElement {

    @property()
    outpostId?: string;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
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
                            <i class="fas fa-question-circle"></i>${gettext("Not available")}
                        </li>
                    </ul>
                </li>`;
            }
            return oh.map((h) => {
                return html`<li>
                    <ul>
                        <li role="cell">
                            <i class="fas fa-check pf-m-success"></i>${gettext(`Last seen: ${h.lastSeen?.toLocaleTimeString()}`)}
                        </li>
                        <li role="cell">
                            ${h.versionOutdated ?
                            html`<i class="fas fa-times pf-m-danger"></i>
                                ${gettext(`${h.version}, should be ${h.versionShould}`)}` :
                            html`<i class="fas fa-check pf-m-success"></i>${gettext(`Version: ${h.version}`)}`}
                        </li>
                    </ul>
                </li>`;
            });
        }), html`<ak-spinner></ak-spinner>`)}</ul>`;
    }

}
