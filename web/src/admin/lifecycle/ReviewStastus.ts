import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { LifecycleIterationStateEnum } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-lifecycle-review-status")
export class ReviewStatus extends AKElement {
    public static styles: CSSResult[] = [PFButton];

    @property()
    status: LifecycleIterationStateEnum = LifecycleIterationStateEnum.UnknownDefaultOpenApi;

    render() {
        return match(this.status)
            .with(
                LifecycleIterationStateEnum.Pending,
                () => html` <ak-label color=${PFColor.Orange}>${msg("Pending review")}</ak-label>`,
            )
            .with(
                LifecycleIterationStateEnum.Reviewed,
                () => html`<ak-label color=${PFColor.Green}>${msg("Reviewed")}</ak-label>`,
            )
            .with(
                LifecycleIterationStateEnum.Overdue,
                () => html`<ak-label color=${PFColor.Red}>${msg("Overdue")}</ak-label>`,
            )
            .with(
                LifecycleIterationStateEnum.Canceled,
                () => html`<ak-label color=${PFColor.Grey}>${msg("Canceled")}</ak-label>`,
            )
            .with(LifecycleIterationStateEnum.UnknownDefaultOpenApi, () => nothing)
            .exhaustive();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-lifecycle-review-status": ReviewStatus;
    }
}
