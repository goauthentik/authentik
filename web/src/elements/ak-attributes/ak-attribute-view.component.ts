import "#elements/ToggleGroup";
import { ToggleGroupEvent } from "#elements/ToggleGroup";
import "./ak-tree-view";

import { match, P } from "ts-pattern";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";

type Mode = "json" | "yaml" | "tree";

const PJsonKey = P.union(P.string, P.number, P.symbol);

type JsonScalar = string | number | boolean | null;

type JsonObject = { [key: string]: JsonValue };

type JsonArray = JsonValue[];

export type JsonValue = JsonScalar | JsonObject | JsonArray;

export class AkAttributeView extends LitElement {
    @property({ attribute: false })
    public value: unknown;

    @property({ type: String, reflect: true })
    public mode: Mode = "json";

    handleToggle = (ev: ToggleGroupEvent<Mode>) => {
        this.mode = ev.value;
    };

    copy = (ev: CustomEvent) => {
        console.log(ev);
    };

    get cleanedValue() {
        const cleanObject = (ob: unknown): JsonValue =>
            match(ob)
                .with(P.string, (s) =>
                    // Clean some artifacts from the way Django sends the data
                    s.replace(/\\n/g, String.fromCharCode(10)).replace(/\\'/g, "'"),
                )
                .with(P.record(PJsonKey, P._), (r) =>
                    Object.fromEntries(
                        Object.entries(r).map(([key, value]) => [`${key}`, cleanObject(value)]),
                    ),
                )
                .with(P.array(P._), (a) => a.map((o) => cleanObject(o)))
                .otherwise((a) => JSON.stringify(a));

        return cleanObject(this.value);
    }

    render() {
        const json = () => html`<pre>${JSON.stringify(this.cleanedValue, null, 2)}</pre>`;

        const yaml = () =>
            html`<pre>${YAML.stringify(this.cleanedValue, { blockQuote: "folded" })}</pre>`;

        return html`
            <ak-toggle-group compact @ak-toggle=${this.handleToggle}>
                <option value="json">${msg("JSON")}</option>
                <option value="yaml">${msg("YAML")}</option>
                <option value="tree">${msg("Tree")}</option>
            </ak-toggle-group>
            <div style="position: relative;">
                <button @click=${this.copy}>Copy</button>
                ${match(this.mode)
                    .with("json", json)
                    .with("yaml", yaml)
                    .with(
                        "tree",
                        () => html`<ak-tree-view .value=${this.cleanedValue}></ak-tree-view>`,
                    )
                    .exhaustive()}
            </div>
        `;
    }
}
