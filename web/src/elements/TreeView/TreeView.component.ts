import Styles from "./TreeView.styles";

import { classList } from "#elements/directives/class-list";
import { getWidthInCh } from "#elements/utils/getWidthInCh";

import { isMatching, match, P } from "ts-pattern";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, LitElement, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { when } from "lit/directives/when.js";

// string, number, object, array, true, false, null

type JsonScalar = string | number | boolean | null;

type JsonObject = { [key: string]: JsonValue };

type JsonArray = JsonValue[];

export type JsonValue = JsonScalar | JsonObject | JsonArray;

export type JsonIndexable = JsonObject | JsonArray;

export type JsonSummary = { count?: number; length?: number };

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

export class TreeView extends LitElement {
    static readonly styles = [Styles];

    @property({ type: Boolean, attribute: "show-expand" })
    showExpand = false;

    @property({ attribute: false })
    public value: JsonValue = null;

    @property({ type: Number, attribute: "summary-maxlength" })
    length = 15;

    @property({ type: Number, attribute: "summary-maxcount" })
    count = 3;

    @state()
    public expanded: Record<string, boolean> = {};

    connectedCallback() {
        super.connectedCallback();

        if (!this.hasAttribute("value") && typeof this.value === "undefined") {
            this.setAttribute("value", this.innerText);
        }

        this.setAttribute("role", "node");
    }

    protected handleClick = (e: Event) => {
        e.preventDefault();

        const clickedPath = ((e.target as Element)?.closest('[part="tree-item"]') as HTMLElement)
            ?.dataset.path;

        if (!clickedPath) {
            console.debug(`ak-tree-view: Could not identify dataset.path from ${e.target}`);

            return;
        }

        this.expanded = { ...this.expanded, [clickedPath]: !this.expanded[clickedPath] };
    };

    jsonSummary(node: JsonIndexable) {
        // Note that `P.string` comes before `stringable` to ensure that overlong strings are truncated
        // correctly.

        const stringSummary = (s: string) =>
            html`"${s.substring(0, length)}${s.length > this.length ? "…" : ""}"`;

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
                .otherwise(() => html`<em>Unknown JSON type</em>`);

        const isArray = Array.isArray(node);
        const allKeys = Object.keys(node);
        const keys = allKeys.slice(0, this.count);

        const summary = [
            ...keys.map((key, index) =>
                [
                    !isArray ? html`${key}:${HS}` : null,
                    getSummary(node),
                    index <= allKeys.length ? html`,${HS}` : null,
                ].filter(noNulls),
            ),
            allKeys.length > this.count ? "…" : null,
        ].filter(noNulls);

        return isArray ? html`[${HS}${summary}${HS}]` : html`{${HS}${summary}${HS}}`;
    }

    renderIndexable(ob: JsonObject | JsonArray, path: string): TemplateResult {
        const entries = Object.entries(ob);

        return html` <ul part="indexable">
            ${entries.map(([key, value]) => {
                const nodePath = path ? `${path}.${key}` : key;
                const scalar = isMatching(PStringable, value);
                const expanded = this.expanded[nodePath];
                const show = scalar || expanded;
                const classes = classList([!scalar && "collapsable", !expanded && "collapsed"]);

                return html`
                    <li
                        part="tree-item"
                        role="treeitem"
                        data-path=${nodePath}
                        aria-expanded=${expanded ? "true" : "false"}
                    >
                        <span
                            part="tree-key"
                            class=${classes}
                            @click=${scalar ? null : this.handleClick}
                        >
                            ${key}:${HS}
                            ${when(Boolean(isJsonIndexable(value) && !expanded), () =>
                                this.renderSummary(value as JsonIndexable),
                            )}
                        </span>
                        ${when(show, () => this.renderValue(value, nodePath))}
                    </li>
                `;
            })}
        </ul>`;
    }

    renderSummary(value: JsonIndexable) {
        return html`<span part="summary">${this.jsonSummary(value)}</span>`;
    }

    renderString(value: string, path = "") {
        const width = getWidthInCh(this);

        // prettier-ignore
        return value.includes("\n") || value.length > width
            ? html`<pre part="multiline-string">${cleanerYaml(value)}</pre>`
            : html`<span part="oneline-string">${cleanerJson(value)}</span>`;
    }

    renderValue(value: JsonValue, path = "") {
        // prettier-ignore
        return match<unknown>(value)
            .with(P.string, (v) => this.renderString(v, path))
            .with(PStringable, (v) => html`"${JSON.stringify(v).replace(/^"/, "").replace(/"$/, "")}"`)
            .with(PIndexable, (v: JsonArray | JsonObject) => this.renderIndexable(v, path))
            .otherwise(() => html`<em>${msg("Unrepresentable")}</em>`);
    }

    render() {
        return html`<div part="tree-viewer">${this.renderValue(this.value)}</div>`;
    }
}
