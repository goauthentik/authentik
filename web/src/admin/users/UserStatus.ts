import "#components/ak-status-label";

import { SlottedTemplateResult } from "#elements/types";

import { CompositeStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderUserStatus(status: CompositeStatusEnum): SlottedTemplateResult {
    switch (status) {
        case CompositeStatusEnum.Active:
            return html`<ak-status-label
                .good=${true}
                .goodLabel=${msg("Active", { id: "user.status.active" })}
            ></ak-status-label>`;
        case CompositeStatusEnum.Locked:
            return html`<ak-status-label
                type="warning"
                .badLabel=${msg("Locked", { id: "user.status.locked" })}
            ></ak-status-label>`;
        case CompositeStatusEnum.PasswordResetPending:
            return html`<ak-status-label
                type="warning"
                .badLabel=${msg("Password reset pending", {
                    id: "user.status.passwordResetPending",
                })}
            ></ak-status-label>`;
        case CompositeStatusEnum.Deactivated:
            return html`<ak-status-label
                .badLabel=${msg("Deactivated", { id: "user.status.deactivated" })}
            ></ak-status-label>`;
        default:
            return html`<ak-status-label
                type="neutral"
                .badLabel=${msg("Unknown", { id: "user.status.unknown" })}
            ></ak-status-label>`;
    }
}
