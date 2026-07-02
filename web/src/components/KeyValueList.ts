import type { SlottedTemplateResult } from "#elements/types";

import { css, html, nothing, type TemplateResult } from "lit";
import { map } from "lit/directives/map.js";

export type KeyValuePair = [term: SlottedTemplateResult, value: SlottedTemplateResult | undefined];

export const keyValueListStyles = css`
    .ak-key-value-list-container {
        container-type: inline-size;
    }

    .ak-key-value-list {
        display: grid;
        gap: var(--pf-global--spacer--lg);
        grid-template-columns: minmax(0, 1fr);
        margin: 0;
    }

    .ak-key-value-list__group {
        min-width: 0;
    }

    .ak-key-value-list__term {
        font-size: var(--pf-c-description-list__term--FontSize, var(--pf-global--FontSize--sm));
        font-weight: var(
            --pf-c-description-list__term--FontWeight,
            var(--pf-global--FontWeight--bold)
        );
        line-height: var(
            --pf-c-description-list__term--LineHeight,
            var(--pf-global--LineHeight--sm)
        );
        margin: 0 0 var(--pf-global--spacer--xs);
    }

    .ak-key-value-list__description {
        margin: 0;
        min-width: 0;
    }

    .ak-key-value-list__value {
        min-width: 0;
        overflow-wrap: anywhere;
    }

    @container (min-width: 30rem) {
        .ak-key-value-list {
            column-gap: var(--pf-global--spacer--lg);
            grid-template-columns: repeat(2, minmax(0, 1fr));
            row-gap: var(--pf-global--spacer--lg);
        }

        .ak-key-value-list__group:nth-child(even) {
            border-left: 1px solid var(--pf-global--BorderColor--100);
            padding-left: var(--pf-global--spacer--lg);
        }
    }
`;

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
