import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { ReviewStateEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-access-review-status")
export class AccessReviewStatus extends AKElement {
    public static styles: CSSResult[] = [PFButton];

    @property()
    status?: ReviewStateEnum;

    render(): TemplateResult {
        switch (this.status) {
            case ReviewStateEnum.Pending:
                return html` <ak-label color=${PFColor.Orange}>${msg("Pending review")}</ak-label>`;
            case ReviewStateEnum.Reviewed:
                return html` <ak-label color=${PFColor.Green}>${msg("Reviewed")}</ak-label>`;
            case ReviewStateEnum.Overdue:
                return html` <ak-label color=${PFColor.Red}>${msg("Overdue")}</ak-label>`;
            case ReviewStateEnum.Canceled:
                return html` <ak-label color=${PFColor.Grey}>${msg("Canceled")}</ak-label>`;
            default:
                return html``;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-access-review-status": AccessReviewStatus;
    }
}
