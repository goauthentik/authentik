import { renderDefault } from "../EventInfo.shared";
import { renderPolicyRequest } from "./renderPolicyException";

import { EventContext, EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";

export function renderPolicyExecution(event: EventWithContext) {
    const result = event.context.result as EventContext;

    const dryRun = event.context.dry_run
        ? html`<ak-label color="pf-m-blue" icon="fa-vial">
              ${msg("Dry-run", {
                  id: "policies.bindings.dry-run.label",
              })}
          </ak-label>`
        : nothing;

    const rawResult =
        result.raw_result !== null && result.raw_result !== undefined
            ? html`<li>
                  ${msg("Raw result", {
                      id: "events.policy-execution.raw-result.label",
                  })}:
                  <pre>${JSON.stringify(result.raw_result, null, 4)}</pre>
              </li>`
            : nothing;

    const cached = event.context.dry_run
        ? html`<li>
              ${msg("Cached", {
                  id: "events.policy-execution.cached.label",
              })}:
              ${event.context.cached ? msg("Yes") : msg("No")}
          </li>`
        : nothing;

    return html`<div class="pf-l-flex">
        ${renderPolicyRequest(event.context as EventContext)}
        <div class="pf-l-flex__item">
            <div class="pf-c-card__title">${msg("Result")} ${dryRun}</div>
            <div class="pf-c-card__body">
                <ul class="pf-c-list">
                    <li>${msg("Passing")}: ${result.passing}</li>
                    <li>
                        ${msg("Messages")}:
                        <ul class="pf-c-list">
                            ${(result.messages as string[]).map((msg) => {
                                return html`<li>${msg}</li>`;
                            })}
                        </ul>
                    </li>
                    ${rawResult} ${cached}
                </ul>
            </div>
        </div>
        <ak-expand>${renderDefault(event)}</ak-expand>
    </div>`;
}
