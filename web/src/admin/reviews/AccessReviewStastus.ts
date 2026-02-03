import {customElement, property} from "lit/decorators.js";
import {AKElement} from "#elements/Base";
import {CSSResult, html, TemplateResult} from "lit";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import {ReviewStateEnum} from "@goauthentik/api";
import {PFColor} from "#elements/Label";
import {msg} from "@lit/localize";

@customElement("ak-access-review-status")
export class AccessReviewStatus extends AKElement {
    public static styles: CSSResult[] = [PFButton];

    @property()
    status?: ReviewStateEnum;

    render(): TemplateResult {
        switch (this.status) {
            case ReviewStateEnum.Pending:
                return html`
                    <ak-label color=${PFColor.Orange}>${msg("Pending review")}</ak-label>`;
            case ReviewStateEnum.Reviewed:
                return html`
                    <ak-label color=${PFColor.Green}>${msg("Reviewed")}</ak-label>`;
            case ReviewStateEnum.Overdue:
                return html`
                    <ak-label color=${PFColor.Red}>${msg("Overdue")}</ak-label>`;
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
