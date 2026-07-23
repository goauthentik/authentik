import "#components/ak-status-label";

import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import AkStatusLabel from "#components/ak-status-label";

import { P4Disposition } from "#styles/patternfly/constants";

import { CompositeStatusEnum } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html } from "lit";

export function UserStatusLabel(status: CompositeStatusEnum): SlottedTemplateResult {
    const props: LitPropertyRecord<AkStatusLabel> = match(status)
        .with(CompositeStatusEnum.Active, () => ({
            type: P4Disposition.Info,
            good: true,
            goodLabel: msg("Active", { id: "user.status.active" }),
        }))
        .with(CompositeStatusEnum.Locked, () => ({
            type: P4Disposition.Warning,
            badLabel: msg("Locked", { id: "user.status.locked" }),
        }))
        .with(CompositeStatusEnum.PasswordResetPending, () => ({
            type: P4Disposition.Warning,
            badLabel: msg("Password reset pending", {
                id: "user.status.password-reset-pending",
            }),
        }))
        .with(CompositeStatusEnum.Deactivated, () => ({
            badLabel: msg("Deactivated", { id: "user.status.deactivated" }),
        }))
        .otherwise(() => ({
            type: P4Disposition.Neutral,
            badLabel: msg("Unknown", { id: "user.status.unknown" }),
        }));

    return html`<ak-status-label ${spread(props)}></ak-status-label>`;
}
