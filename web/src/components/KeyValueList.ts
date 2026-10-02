import type { SlottedTemplateResult } from "#elements/types";

import Styles from "#components/KeyValueList.css";

import { html, nothing, type TemplateResult } from "lit";
import { map } from "lit/directives/map.js";

export type KeyValuePair = [term: SlottedTemplateResult, value: SlottedTemplateResult | undefined];

export const keyValueListStyles = Styles;

function renderKeyValueGroup([term, value]: KeyValuePair) {
    return html`<div class="ak-key-value-list__group">
        <dt class="ak-key-value-list__term">${term}</dt>
        <dd class="ak-key-value-list__description">
            <div class="ak-key-value-list__value">${value ?? nothing}</div>
        </dd>
    </div>`;
}

export function renderKeyValueList(items: KeyValuePair[]): TemplateResult {
    return html`<div class="ak-key-value-list-container">
        <dl class="ak-key-value-list">${map(items, renderKeyValueGroup)}</dl>
    </div>`;
}
