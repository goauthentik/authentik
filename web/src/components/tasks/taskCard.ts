/**
 * @file A function that returns a TaskList ready to drop into any view
 */

import "#components/tasks/TaskList";
import "#elements/cards/SectionCard";
import { ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function taskCard(model: ModelEnum, objId: string | number | undefined) {
    const [appLabel, modelName] = model.split(".");

    return html`<ak-section-card label=${msg("Tasks")}>
        <ak-task-list
            .relObjAppLabel=${appLabel}
            .relObjModel=${modelName}
            .relObjId=${objId}
        ></ak-task-list>
    </ak-section-card>`;
}
