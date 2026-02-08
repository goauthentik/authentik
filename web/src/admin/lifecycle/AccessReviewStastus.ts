import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { ReviewStateEnum } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-access-review-status")
export class AccessReviewStatus extends AKElement {
    public static styles: CSSResult[] = [PFButton];

    @property()
    status: ReviewStateEnum = ReviewStateEnum.UnknownDefaultOpenApi;

    render() {
        return match(this.status)
            .with(
                ReviewStateEnum.Pending,
                () => html` <ak-label color=${PFColor.Orange}>${msg("Pending review")}</ak-label>`,
            )
            .with(
                ReviewStateEnum.Reviewed,
                () => html`<ak-label color=${PFColor.Green}>${msg("Reviewed")}</ak-label>`,
            )
            .with(
                ReviewStateEnum.Overdue,
                () => html`<ak-label color=${PFColor.Red}>${msg("Overdue")}</ak-label>`,
            )
            .with(
                ReviewStateEnum.Canceled,
                () => html`<ak-label color=${PFColor.Grey}>${msg("Canceled")}</ak-label>`,
            )
            .with(ReviewStateEnum.UnknownDefaultOpenApi, () => nothing)
            .exhaustive();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-access-review-status": AccessReviewStatus;
    }
}
