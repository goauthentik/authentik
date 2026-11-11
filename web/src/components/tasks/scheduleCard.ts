/**
 * @file A function that returns a ScheduleList ready to drop into any view
 */

import "#components/tasks/ScheduleList";
import "#elements/cards/SectionCard";
import { ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function scheduleCard(model: ModelEnum, objId: string | number | undefined) {
    const [appLabel, modelName] = model.split(".");

    return html` <ak-section-card label=${msg("Schedules")}>
        <ak-schedule-list
            .relObjAppLabel=${appLabel}
            .relObjModel=${modelName}
            .relObjId=${objId}
        ></ak-schedule-list>
    </ak-section-card>`;
}
