import { TemplateResult, html, nothing } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

type DescriptionDesc = string | TemplateResult | typeof nothing;
type DescriptionPair = [string, DescriptionDesc];
type DescriptionRecord = { term: string; desc: DescriptionDesc };

interface DescriptionConfig {
    horizontal: boolean;
    compact: boolean;
    twocolumn: boolean;
    threecolumn: boolean;
}

const isDescriptionRecordCollection = (v: Array<any>): v is DescriptionRecord[] =>
    v.length > 0 && typeof v[0] === "object" && !Array.isArray(v[0]);

function renderDescriptionGroup([term, description]: DescriptionPair) {
    return html` <div class="pf-c-description-list__group">
        <dt class="pf-c-description-list__term">
            <span class="pf-c-description-list__text">${term}</span>
        </dt>
        <dd class="pf-c-description-list__description">
            <div class="pf-c-description-list__text">${description}</div>
        </dd>
    </div>`;
}

function recordToPair({ term, desc }: DescriptionRecord): DescriptionPair {
    return [term, desc];
}

function alignTermType(terms: DescriptionRecord[] | DescriptionPair[] = []) {
    if (isDescriptionRecordCollection(terms)) {
        return terms.map(recordToPair);
    }
    return terms ?? [];
}

export function renderDescriptionList(
    terms: DescriptionRecord[] | DescriptionPair[] = [],
    config: DescriptionConfig = {
        horizontal: false,
        compact: false,
        twocolumn: false,
        threecolumn: false,
    }
) {
    const checkedTerms = alignTermType(terms);
    const classes = classMap({
        "pf-m-horizontal": config.horizontal,
        "pf-m-compact": config.compact,
        "pf-m-2-col-on-lg": config.twocolumn,
        "pf-m-3-col-on-lg": config.threecolumn,
    });

    return html`
        <dl class="pf-c-description-list ${classes}">
            ${map(checkedTerms, renderDescriptionGroup)}
        </dl>
    `;
}
