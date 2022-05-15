import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../Tooltip";

@customElement("ak-utils-time-delta-help")
export class TimeDeltaHelp extends LitElement {
    @property({ type: Boolean })
    negative = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFList, AKGlobal];
    }

    render(): TemplateResult {
        return html` <ak-tooltip>
            <p class="pf-c-form__helper-text" slot="trigger">
                ${this.negative
                    ? t`(Format: hours=-1;minutes=-2;seconds=-3).`
                    : t`(Format: hours=1;minutes=2;seconds=3).`}
                <i class="pf-icon fa fa-question-circle" aria-hidden="true"></i>
            </p>

            <div slot="tooltip">
                ${t`The following keywords are supported:`}
                <ul class="pf-c-list">
                    <li><pre>microseconds</pre></li>
                    <li><pre>milliseconds</pre></li>
                    <li><pre>seconds</pre></li>
                    <li><pre>minutes</pre></li>
                    <li><pre>hours</pre></li>
                    <li><pre>days</pre></li>
                    <li><pre>weeks</pre></li>
                </ul>
            </div>
        </ak-tooltip>`;
    }
}
