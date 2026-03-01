import "#components/ak-status-label";

import { AKElement } from "#elements/Base";

import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

import { isMatching, match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

/**
 * Formats a value for display based on its type.
 */
function formatValue(value: unknown): TemplateResult | string {
    const jsonify = (v: Record<string | number | symbol, unknown> | unknown[]) =>
        html`<code>
            <pre style="margin: 0; white-space: pre-wrap;">${JSON.stringify(v, null, 2)}</pre>
        </code>`;

    const Stringable = P.union(P.string, P.number);
    const isStringable = (s: unknown) => isMatching(Stringable, s);
    const isStringableArray = (a: unknown[]) => a.every(isStringable);

    return match(value)
        .with(P.nullish, () => "-")
        .with(P.boolean, (v) => html`<ak-status-label ?good=${v}></ak-status-label>`)
        .with(Stringable, (v) => String(v))
        .with(P.array(), (v) => (isStringableArray(v) ? v.join(", ") : jsonify(v)))
        .with(P.record(P.string, P.any), (v) => jsonify(v))
        .otherwise((v) => String(v));
}

/**
 * A reusable card component to display custom attributes for objects like User, Group, or Device.
 *
 * This component filters out system attributes (keys starting with `goauthentik.io/`)
 * and optionally excludes the `notes` attribute (since it's typically displayed separately).
 *
 * Value types are rendered appropriately:
 * - string/number: Plain text
 * - boolean: ak-status-label component
 * - simple arrays: Comma-separated list
 * - objects/complex arrays: Formatted JSON in code block
 */
@customElement("ak-object-attributes-card")
export class ObjectAttributesCard extends AKElement {
    static styles: CSSResult[] = [PFCard, PFDescriptionList];

    @property({ attribute: false })
    objectAttributes: Record<string, unknown> = {};

    @property({ type: Boolean, attribute: "exclude-notes" })
    excludeNotes = true;

    /**
     * Filters the attributes to only include custom (non-system) attributes.
     * Excludes keys starting with "goauthentik.io/" and optionally the "notes" key.
     */
    private get customAttributes(): Array<[string, unknown]> {
        return Object.entries(this.objectAttributes || {}).filter(([key]) => {
            if (key.startsWith("goauthentik.io/")) return false;
            if (this.excludeNotes && key === "notes") return false;
            return true;
        });
    }

    render() {
        const attrs = this.customAttributes;

        return html`
            <div class="pf-c-card__title">${msg("Custom Attributes")}</div>
            <div class="pf-c-card__body">
                ${attrs.length > 0
                    ? renderDescriptionList(
                          attrs.map(([key, value]) => [
                              key,
                              formatValue(value),
                          ]) as DescriptionPair[],
                          { horizontal: true },
                      )
                    : html`<p>${msg("No custom attributes defined.")}</p>`}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-attributes-card": ObjectAttributesCard;
    }
}
