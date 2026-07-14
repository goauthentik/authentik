/**
 * @file A function that returns a TaskList ready to drop into any view
 */

import "#components/tasks/TaskList";

import { ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function taskCard(model: ModelEnum, objId: string | number | undefined) {
    const [appLabel, modelName] = model.split(".");
    return html`<div class="pf-c-card">
        <div class="pf-c-card__header">
            <div class="pf-c-card__title">${msg("Tasks")}</div>
        </div>
        </div>
        <ak-task-list .relObjAppLabel=${appLabel} .relObjModel=${modelName} .relObjId=${objId}></ak-task-list>
    </div>`;
}
