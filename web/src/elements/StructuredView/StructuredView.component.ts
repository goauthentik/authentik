import Styles from "./StructuredView.styles";

import { match, P } from "ts-pattern";
import YAML from "yaml";

import { msg, str } from "@lit/localize";
import { html, LitElement, nothing, type TemplateResult } from "lit";
import { property } from "lit/decorators.js";

// string, number, object, array, true, false, null

type JsonScalar = string | number | boolean | null;

type JsonObject = { [key: string]: JsonValue };

type JsonArray = JsonValue[];

export type JsonValue = JsonScalar | JsonObject | JsonArray;

export type JsonIndexable = JsonObject | JsonArray;

const isJsonArray = (v: unknown): v is JsonArray => Array.isArray(v);

const isJsonObject = (v: unknown): v is JsonObject =>
    v !== null && !Array.isArray(v) && typeof v === "object";

const isJsonIndexable = (v: unknown): v is JsonIndexable => isJsonArray(v) || isJsonObject(v);
const PStringable = P.union(P.string, P.number, P.boolean, P.nullish);
const PIndexable = P.union(P.when(isJsonArray), P.when(isJsonObject));
const noNulls = (n: unknown) => n !== null;
const cleanerJson = (s: string) => JSON.stringify(s).replace(/^"/m, "").replace(/"$/m, "");
const cleanerYaml = (value: string) => YAML.stringify(value).replace(/^>- *\n*/, "");
const HS = " ";

/**
 * @element ak-structured-view
 * @summary A "pretty" view of structured data
 *
 * Pass the value to display with the `value` property.
 *
 * @attr {number} summary-maxlength - Longest string shown in a collapsed summary (default 15)
 * @attr {number} summary-maxcount - Most entries shown in a collapsed summary (default 3)
 * @attr {boolean} show-count - Show total count of keys next to summaries
 *
 * @csspart structured-viewer - The outermost container
 * @csspart indexable - The list of entries in an object or array
 * @csspart tree-item - One entry in an object or array
 * @csspart tree-key - An entry's key: a `<span>` for scalars, the `<summary>` for objects and
 *   arrays
 * @csspart summary - The preview of a collapsed object or array
 * @csspart oneline-string - A string without line breaks
 * @csspart multiline-string - A string with line breaks, shown preformatted
 *
 * See the `StructuredView.root.css` file in this folder for the CSS Custom Properties that
 * control the appearance of this component.
 */
export class StructuredView extends LitElement {
    static readonly styles = [Styles];

    @property({ attribute: false })
    public value: JsonValue = null;

    @property({ type: Number, attribute: "summary-maxlength" })
    length = 15;

    @property({ type: Number, attribute: "summary-maxcount" })
    count = 3;

    @property({ type: Boolean, attribute: "show-count" })
    showCount = false;

    protected openNodes = new WeakSet<JsonIndexable>();

    protected handleToggle(node: JsonIndexable, ev: Event) {
        if ((ev.currentTarget as HTMLDetailsElement).open) {
            this.openNodes.add(node);
        } else {
            this.openNodes.delete(node);
        }

        this.requestUpdate();
    }

    jsonSummary(node: JsonIndexable) {
        // Note that `P.string` comes before `stringable` to ensure that overlong strings are
        // truncated correctly.

        const stringSummary = (s: string) =>
            html`"${s.substring(0, this.length)}${s.length > this.length ? "…" : ""}"`;

        // prettier-ignore
        const getSummary = (node: unknown) =>
            match(node)
                .with(P.array(), (node) => node.length === 0 ? html`[${HS}]` : html`[${HS}…${HS}]`)
                .with(P.string,  (node) => stringSummary(node))
                .with(PStringable, (node) => JSON.stringify(node))
                .when(isJsonObject,
                    () => Object.keys(node as JsonObject).length === 0
                        ? html`{${HS}}`
                        : html`{${HS}…${HS}}`,
                )
                .otherwise(
                    () => html`<em>${msg("Unknown JSON type", {
                        id: "data-view.summary.unknown-type.label",
                    })}</em>`,
                );

        const isArray = Array.isArray(node);
        const allEntries = Object.entries(node);
        const entries = allEntries.slice(0, this.count);
        const count = allEntries.length;

        const summary = [
            ...entries.map(([key, value], index) =>
                [
                    !isArray ? html`${key}:${HS}` : null,
                    getSummary(value),
                    index < count - 1 ? html`,${HS}` : null,
                ].filter(noNulls),
            ),
            count > this.count ? "…" : null,
        ].filter(noNulls);

        const keySummaryState = {
            plural: count > 1,
            array: isArray,
        };

        const wr = (c: string) => html`<span part="keycount">(${c})</span>`;

        const keyMesg =
            this.showCount && count > 0
                ? match(keySummaryState)
                      .with({ array: true, plural: false }, () => wr(msg(str`${count} item`)))
                      .with({ array: true, plural: true }, () => wr(msg(str`${count} items`)))
                      .with({ array: false, plural: false }, () => wr(msg(str`${count} key`)))
                      .with({ array: false, plural: true }, () => wr(msg(str`${count} keys`)))
                      .exhaustive()
                : "";

        return isArray
            ? html`[${HS}${summary}${HS}]${HS}${keyMesg}`
            : html`{${HS}${summary}${HS}}${HS}${keyMesg}`;
    }

    renderIndexable(ob: JsonObject | JsonArray, path: string): TemplateResult {
        return html`<ul part="indexable">
            ${Object.entries(ob).map(([key, value]) => {
                const nodePath = path ? `${path}.${key}` : key;

                if (!isJsonIndexable(value)) {
                    return html`<li part="tree-item" data-path=${nodePath}>
                        <span part="tree-key">${key}:${HS}</span
                        >${this.renderValue(value, nodePath)}
                    </li>`;
                }

                const open = this.openNodes.has(value);

                return html`<li part="tree-item" data-path=${nodePath}>
                    <details ?open=${open} @toggle=${(ev: Event) => this.handleToggle(value, ev)}>
                        <summary part="tree-key">
                            ${key}:${HS}${open ? nothing : this.renderSummary(value)}
                        </summary>
                        ${open ? this.renderValue(value, nodePath) : nothing}
                    </details>
                </li>`;
            })}
        </ul>`;
    }

    renderSummary(value: JsonIndexable) {
        return html`<span part="summary">${this.jsonSummary(value)}</span>`;
    }

    renderString(value: string) {
        // prettier-ignore
        return value.includes("\n")
            ? html`<pre part="multiline-string">${cleanerYaml(value)}</pre>`
            : html`<span part="oneline-string">${cleanerJson(value)}</span>`;
    }

    renderValue(value: JsonValue, path = "") {
        // prettier-ignore
        return match<unknown>(value)
            .with(P.string, (v) => this.renderString(v))
            .with(PStringable, (v) => String(v))
            .with(PIndexable, (v: JsonArray | JsonObject) => this.renderIndexable(v, path))
            .otherwise(
                () => html`<em>${msg("Unrepresentable", {
                    id: "data-view.value.unrepresentable.label",
                })}</em>`,
            );
    }

    render() {
        return html`<div part="structured-viewer">${this.renderValue(this.value)}</div>`;
    }
}
