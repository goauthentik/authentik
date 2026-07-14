import Styles from "./ak-tree-view.styles";

import { classList } from "#elements/directives/class-list";

import { isMatching, match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { html, LitElement, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

// string, number, object, array, true, false, null

type JsonScalar = string | number | boolean | null;
type JsonObject = { [key: string]: JsonValue };
type JsonArray = JsonValue[];
export type JsonValue = JsonScalar | JsonObject | JsonArray;

const isJsonArray = (v: unknown): v is JsonArray => Array.isArray(v);
const isJsonObject = (v: unknown): v is JsonObject => v !== null && !Array.isArray(v) && typeof v === "object";
const PStringable = P.union(P.string, P.number, P.boolean, P.nullish);
const PIndexable = P.union(P.when(isJsonArray), P.when(isJsonObject));

@customElement("ak-tree-view")
export class AkAttributeView extends LitElement {
    static readonly styles = [Styles];

    @property({ type: Boolean, attribute: "show-expand" })
    showExpand = false;

    @property({ attribute: false })
    public value: JsonValue = null;

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
        const clickedPath = ((e.target as Element)?.closest('[part="tree-item"]') as HTMLElement)?.dataset.path;
        if (!clickedPath) {
            console.debug(`ak-tree-view: Could not identify dataset.path from ${e.target}`);
            return;
        }
        this.expanded = { ...this.expanded, [clickedPath]: !this.expanded[clickedPath] };
    };

    renderIndexable(ob: JsonObject | JsonArray, path: string): TemplateResult {
        const entries = Object.entries(ob);

        return html` <ul part="indexable">
            ${entries.map(([key, value]) => {
                const nodePath = path ? `${path}.${key}` : key;
                const scalar = isMatching(PStringable, value);
                const expanded = this.expanded[nodePath];
                const show = scalar || expanded;
                const classes = classList([!scalar && "collapsable", !this.expanded && "collapsed"]);

                return html`
                    <li
                        part="tree-item"
                        role="treeitem"
                        data-path=${nodePath}
                        aria-expanded=${expanded ? "true" : "false"}
                    >
                        <span part="tree-key" class=${classes} @click=${scalar ? null : this.handleClick}> </span>
                        ${key}: ${show ? this.renderValue(value, nodePath) : this.renderPreview(value)}
                    </li>
                `;
            })}
        </ul>`;
    }

    renderPreview(v: JsonObject | JsonArray) {
        return Array.isArray(v) ? html`[${msg("Array")}]` : html`{${msg("Object")}}`;
    }

    renderValue(value: JsonValue, path = "") {
        // @ts-ignore
        return match(value)
            .with(PStringable, (v) => html`${JSON.stringify(v).replace(/^"/, "").replace(/"$/, "")}`)
            .with(PIndexable, (v: JsonArray | JsonObject) => this.renderIndexable(v, path))
            .otherwise(() => html`<em>${msg("Unrepresentable")}</em>`);
    }

    render() {
        return html`<div part="tree-viewer">${this.renderValue(this.value)}</div>`;
    }
}
