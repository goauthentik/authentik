import { getModelInfo, renderDefault } from "../EventInfo.shared";

import { EventModel, EventWithContext } from "#common/events";

import { match, P } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { html } from "lit";

type DiffEntry = {
    new_value: unknown;
    previous_value: unknown;
    add?: string[];
    remove?: string[];
    clear?: boolean;
};

type DiffRecord = {
    [key: string]: DiffEntry;
};

const makeList = (value: string[], m: (s: string) => string) => html`<ul class="pf-c-list">
    ${value.map((item) => html`<li>${m(item)}</li>`)}
</ul>`;

function newCol(key: string, value: DiffEntry) {
    // prettier-ignore
    const newVal = match(value)
        .with({ add: P.nonNullable }, ({ add }) => makeList(add, (i) => msg(str`Added ID ${i}`)))
        .with({ remove: P.nonNullable }, ({ remove }) => makeList(remove, (i) => msg(str`Removed ID ${i}`)))
        .with({ clear: true }, () => msg("Cleared"))
        .otherwise(({ new_value }) => html`<pre>${JSON.stringify(new_value, null, 4)}</pre>`);

    const previousVal =
        value.previous_value !== null ? JSON.stringify(value.previous_value, null, 4) : msg("-");

    return html`<tr>
        <td><pre>${key}</pre></td>
        <td><pre>${previousVal}</pre></td>
        <td>${newVal}</td>
    </tr>`;
}

const renderDiff = (diff: DiffRecord | undefined | null) =>
    diff
        ? html`<div class="pf-l-split__item pf-m-fill">
              <div class="pf-c-card__title">${msg("Changes made:")}</div>
              <table class="pf-c-table pf-m-compact pf-m-grid-md">
                  <thead>
                      <tr>
                          <th scope="col">${msg("Key")}</th>
                          <th scope="col">${msg("Previous value")}</th>
                          <th scope="col">${msg("New value")}</th>
                      </tr>
                  </thead>
                  <tbody role="rowgroup">
                      ${Object.entries(diff).map(([key, value]) => newCol(key, value))}
                  </tbody>
              </table>
          </div>`
        : null;

export function renderModelChanged(event: EventWithContext) {
    return html`
        <div class="pf-l-split">
            <div class="pf-l-split__item pf-m-fill">
                <div class="pf-c-card__title">${msg("Affected model:")}</div>
                <div class="pf-c-card__body">
                    ${getModelInfo(event.context?.model as EventModel)}
                </div>
            </div>
            ${renderDiff(event.context?.diff as unknown as DiffRecord | null | undefined)}
        </div>
        <br />
        <ak-expand>${renderDefault(event)}</ak-expand>
    `;
}
