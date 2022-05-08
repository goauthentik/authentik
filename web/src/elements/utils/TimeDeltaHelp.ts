import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/Form.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-utils-time-delta-help")
export class TimeDeltaHelp extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFForm, AKGlobal];
    }

    render(): TemplateResult {
        return html`<p class="pf-c-form__helper-text">
            ${t`(Format: hours=-1;minutes=-2;seconds=-3).`}
        </p>`;
    }
}
