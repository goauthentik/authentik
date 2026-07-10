import "#components/ak-toggle-group";

import { match, P } from "ts-pattern";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";

type Mode = "json" | "yaml"; // "tree"

const PJsonKey = P.union(P.string, P.number, P.symbol);

export class AkAttributeView extends LitElement {
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
