import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { Outpost } from "../../api/Outposts";
import { COMMON_STYLES } from "../../common/styles";

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
        return html`<ul>${until(Outpost.health(this.outpostId).then((oh) => {
            if (oh.length === 0) {
                return html`<li>
                    <ul>
                        <li role="cell">
                            <i class="fas fa-question-circle"></i>&nbsp;${gettext("Not available")}
                        </li>
                    </ul>
                </li>`;
            }
            return oh.map((h) => {
                return html`<li>
                    <ul>
                        <li role="cell">
                            <i class="fas fa-check pf-m-success"></i>&nbsp;${gettext(`Last seen: ${new Date(h.last_seen * 1000).toLocaleTimeString()}`)}
                        </li>
                        <li role="cell">
                            ${h.version_outdated ?
                            html`<i class="fas fa-times pf-m-danger"></i>&nbsp;
                                ${gettext(`${h.version}, should be ${h.version_should}`)}` :
                            html`<i class="fas fa-check pf-m-success"></i>&nbsp;${gettext(`Version: ${h.version}`)}`}
                        </li>
                    </ul>
                </li>`;
            });
        }), html`<ak-spinner></ak-spinner>`)}</ul>`;
    }

}
