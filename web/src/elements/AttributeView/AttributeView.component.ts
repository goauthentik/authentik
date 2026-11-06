import "#elements/ToggleGroup";
import Styles from "./AttributeView.styles";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "../ak-tree-view";

import { writeToClipboard } from "#common/clipboard";

import { ToggleGroupEvent } from "#elements/ToggleGroup";

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
    static readonly styles = [Styles];

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

    // prettier-ignore
    copyIcon = html`<!-- © fontawesome. CC-BY-4.0 licensed --><svg xmlns="http://www.w3.org/2000/svg" data-icon-name="copy" height="512" width="448" viewBox="0 0 448 512"><path d="M320 448v40c0 13.255-10.745 24-24 24H24c-13.255 0-24-10.745-24-24V120c0-13.255 10.745-24 24-24h72v296c0 30.879 25.121 56 56 56h168zm0-344V0H152c-13.255 0-24 10.745-24 24v368c0 13.255 10.745 24 24 24h272c13.255 0 24-10.745 24-24V128H344c-13.2 0-24-10.8-24-24zm120.971-31.029L375.029 7.029A24 24 0 0 0 358.059 0H352v96h96v-6.059a24 24 0 0 0-7.029-16.97z" /></svg>`;

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

    async handleCopy() {
        const value =
            this.mode === "yaml"
                ? YAML.stringify(this.cleanedValue)
                : JSON.stringify(this.cleanedValue);

        const res = await writeToClipboard(value, msg("Attributes"));
        console.log(res);
    }

    render() {
        const json = () => html`<pre>${JSON.stringify(this.cleanedValue, null, 2)}</pre>`;

        const yaml = () =>
            html`<pre>${YAML.stringify(this.cleanedValue, { blockQuote: "folded" })}</pre>`;

        return html`
            <div part="toolbar">
                <ak-toggle-group compact value=${this.mode} @ak-toggle=${this.handleToggle}>
                    <option value="json">${msg("JSON")}</option>
                    <option value="yaml">${msg("YAML")}</option>
                    <option value="tree">${msg("Tree")}</option>
                </ak-toggle-group>
                <button
                    class="pf-c-button pf-m-plain"
                    type="button"
                    part="copy-button"
                    @click=${() => this.handleCopy()}
                    aria-label=${msg("Copy attributes to clipboard")}
                >
                    <pf-tooltip position="top" content=${msg("Copy attributes to clipboard")}
                        >${this.copyIcon}
                    </pf-tooltip>
                </button>
            </div>
            <div part="display">
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
