import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";

// string, number, object, array, true, false, null

type JsonScalar = string | number | boolean | null;
type JsonObject = { [key: string]: JsonValue };
type JsonArray = JsonValue[];
export type JsonValue = JsonScalar | JsonObject | JsonArray;

@customElement("ak-tree-view")
export class AkAttributeView extends LitElement {
    @property({ type: Boolean, attribute: "show-expand" })
    showExpand = false;

    @property({ attribute: false })
    public value: unknown;

    @property({ attribute: false })
    public value: unknown;

    @property({ type: String, reflect: true })
    public mode: Mode = "json";

    handleToggle = (ev: CustomEvent) => {
        this.mode = ev.detail.value;
    };

    get cleanedValue() {
        const cleanObject = (ob: unknown) =>
            match(ob)
                .with(P.string, (s) =>
                    // Clean some artifacts from the way Django sends the data
                    s.replace(/\\n/g, String.fromCharCode(10)).replace(/\\'/g, "'")
                )
                .with(P.record(PJsonKey, P._), (r) =>
                    Object.fromEntries(
                        Object.entries(r).map(([key, value]) => [key, cleanObject(value)])
                    )
                )
                .with(P.array(P._), (a) => a.map((o) => cleanObject(o)))
                .otherwise((a) => a);
        return cleanObject(this.value);
    }

    render() {
        const json = () => JSON.stringify(this.cleanedValue, null, 2);
        const yaml = () => YAML.stringify(this.cleanedValue, { blockQuote: "folded" });

        return html`
            <ak-toggle-group compact @ak-toggle=${this.handleToggle}>
                <option value="json">${msg("JSON")}</option>
                <option value="yaml">${msg("YAML")}</option>
            </ak-toggle-group>
            <div style="position: relative;">
                <button @click=${() => this.copy(this.mode === "json" ? json : yaml)}>Copy</button>
                <pre>${this.mode === "json" ? json() : yaml()}</pre>
            </div>
        `;
    }
}
