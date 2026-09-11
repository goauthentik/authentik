/**
 * @file A function that returns a ScheduleList ready to drop into any view
 */

import "#components/tasks/ScheduleList";

import { ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function scheduleCard(model: ModelEnum, objId: string | number | undefined) {
    const [appLabel, modelName] = model.split(".");

    return html`<div class="pf-c-card">
        <div class="pf-c-card__header">
            <div class="pf-c-card__title">${msg("Schedules")}</div>
        </div>
        <ak-schedule-list
            .relObjAppLabel=${appLabel}
            .relObjModel=${modelName}
            .relObjId=${objId}
        ></ak-schedule-list>
    </div>`;
}
