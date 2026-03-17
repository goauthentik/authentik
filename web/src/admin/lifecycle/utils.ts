import { PFColor } from "#elements/Label";
import { LitFC } from "#elements/types";

import { LifecycleIterationStateEnum } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html } from "lit";

export interface LifecycleIterationStatusProps {
    status?: LifecycleIterationStateEnum;
}

export const LifecycleIterationStatus: LitFC<LifecycleIterationStatusProps> = ({ status }) => {
    return match(status)
        .with(
            LifecycleIterationStateEnum.Pending,
            () => html`<ak-label color=${PFColor.Orange}>${msg("Pending review")}</ak-label>`,
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
        .otherwise(() => html`<ak-label color=${PFColor.Grey}>${msg("Unknown")}</ak-label>`);
};
