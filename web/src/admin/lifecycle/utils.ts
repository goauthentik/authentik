import "#components/ak-status-label";

import { MessageFormatter } from "#common/ui/locale/format";

import { PFColor } from "#elements/Label";
import { LitFC, LitPropertyRecord } from "#elements/types";

import AkStatusLabel from "#components/ak-status-label";

import { P4Disposition } from "#styles/patternfly/constants";

import {
    LifecycleIterationStateEnum,
    OffboardingActionEnum,
    OffboardingStatusEnum,
} from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
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
            () => html`<ak-label color=${PFColor.Gray}>${msg("Canceled")}</ak-label>`,
        )
        .otherwise(() => html`<ak-label color=${PFColor.Gray}>${msg("Unknown")}</ak-label>`);
};

export interface OffboardingStatusProps {
    status?: OffboardingStatusEnum;
}

export const OffboardingStatus: LitFC<OffboardingStatusProps> = ({ status }) => {
    const props: LitPropertyRecord<AkStatusLabel> = match(status)
        .with(OffboardingStatusEnum.Completed, () => ({
            ".good": true,
            ".goodLabel": msg("Completed"),
        }))
        .with(OffboardingStatusEnum.Pending, () => ({
            ".type": P4Disposition.Warning,
            ".badLabel": msg("Pending"),
        }))
        .with(OffboardingStatusEnum.Failed, () => ({
            ".type": P4Disposition.Error,
            ".badLabel": msg("Failed"),
        }))
        .with(OffboardingStatusEnum.Canceled, () => ({
            ".type": P4Disposition.Neutral,
            ".badLabel": msg("Canceled"),
        }))
        .otherwise(() => ({
            ".type": P4Disposition.Neutral,
            ".badLabel": msg("Unknown"),
        }));

    return html`<ak-status-label ${spread(props)}></ak-status-label>`;
};

const OffboardingActionLabelRecord: Record<OffboardingActionEnum, MessageFormatter<string>> = {
    [OffboardingActionEnum.Deactivate]: () => msg("Deactivate"),
    [OffboardingActionEnum.Delete]: () => msg("Delete"),
    [OffboardingActionEnum.UnknownDefaultOpenApi]: () => msg("Unknown"),
};

export function offboardingActionLabel(
    action: OffboardingActionEnum = OffboardingActionEnum.UnknownDefaultOpenApi,
): string {
    return OffboardingActionLabelRecord[action]();
}
