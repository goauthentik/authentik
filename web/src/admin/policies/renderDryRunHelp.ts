import { toAdminInterface } from "#elements/router/core/interfaces";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderDryRunHelp() {
    return msg(
        html`Evaluate this binding without including its result or messages in the final decision.
            Results are recorded in the <a href=${toAdminInterface("events/log")}>Event Log</a>.
            Expression policies can still make network requests, create events, or modify data.`,
        { id: "policies.bindings.dry-run.description" },
    );
}
