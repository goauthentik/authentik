import "#elements/ToggleGroup";
import Styles from "./AttributeView.styles";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "../ak-structured-view";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

import { writeToClipboard } from "#common/clipboard";

import { AKElement } from "#elements/Base";
import type { JsonValue } from "#elements/StructuredView/StructuredView.component";
import { ToggleGroupEvent } from "#elements/ToggleGroup";

import { match, P } from "ts-pattern";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, type PropertyValues } from "lit";
import { property } from "lit/decorators.js";

const MODES = ["json", "yaml", "tree"] as const;

type Mode = (typeof MODES)[number];

const PJsonKey = P.union(P.string, P.number, P.symbol);

/**
 * @element ak-attribute-view
 * @summary Provides different views of structured data, switchable between JSON, YAML and
 *   ak-structured-view.
 *
 * Set the value to display with the `value` property; it has no attribute.
 *
 * @attr {string} mode - Display format: "json" (default), "yaml" or "tree".
 * @attr {boolean} hide-copy - Hides the copy-to-clipboard button
 * @attr {boolean} show-count - In tree mode, shows how many keys or items each collapsed summary
 *   hides
 *
 * @csspart toolbar - The row holding the format toggle and the copy button
 * @csspart copy-button - The copy-to-clipboard button
 * @csspart copy-tooltip - The tooltip wrapping the copy button's icon
 * @csspart display - The container for the rendered JSON, YAML or tree
 *
 * See the `AttributeView.root.css` file in this folder for the CSS Custom Properties that
 * control the appearance of this component.
 */
export class AkAttributeView extends AKElement {
    static readonly styles = [PFButton, Styles];

    @property({ attribute: false })
    public value: unknown;

    @property({ type: String, reflect: true })
    public mode: Mode = "json";

    @property({ type: Boolean, attribute: "hide-copy" })
    public hideCopy = false;

    @property({ type: Boolean, attribute: "show-count" })
    public showCount = false;

    handleToggle = (ev: ToggleGroupEvent<Mode>) => {
        this.mode = ev.value;
    };

    protected override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);

        // `mode` is a public attribute, so it can hold anything; fall back rather than fail render.
        if (changed.has("mode") && !MODES.includes(this.mode)) {
            this.mode = "json";
        }
    }

    // prettier-ignore
    copyIcon = html`<i class="fas fa-copy"></i>`;

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
                .with(P.union(P.number, P.boolean, null), (v) => v)
                .otherwise((a) => JSON.stringify(a));

        return cleanObject(this.value);
    }

    // Copy what the server sent; the unescaping in `cleanedValue` is for display only.
    handleCopy() {
        const [value, kind] =
            this.mode === "yaml"
                ? [YAML.stringify(this.value), msg("YAML", { id: "data-view.format.yaml.label" })]
                : [
                      JSON.stringify(this.value, null, 2),
                      msg("JSON", { id: "data-view.format.json.label" }),
                  ];

        return writeToClipboard(value, kind);
    }

    render() {
        const json = () => html`<pre>${JSON.stringify(this.cleanedValue, null, 2)}</pre>`;

        const yaml = () =>
            html`<pre>${YAML.stringify(this.cleanedValue, { blockQuote: "folded" })}</pre>`;

        const label =
            this.mode === "yaml"
                ? msg("Copy YAML to clipboard", { id: "data-view.copy.yaml.label" })
                : msg("Copy JSON to clipboard", { id: "data-view.copy.json.label" });

        return html`
            <div part="toolbar">
                <ak-toggle-group compact value=${this.mode} @ak-toggle=${this.handleToggle}>
                    <option value="json">
                        ${msg("JSON", { id: "data-view.format.json.label" })}
                    </option>
                    <option value="yaml">
                        ${msg("YAML", { id: "data-view.format.yaml.label" })}
                    </option>
                    <option value="tree">
                        ${msg("Tree", { id: "data-view.format.tree.label" })}
                    </option>
                </ak-toggle-group>
                ${
                    this.hideCopy
                        ? null
                        : html`
                              <button
                                  class="pf-c-button pf-m-plain"
                                  type="button"
                                  part="copy-button"
                                  @click=${() => this.handleCopy()}
                                  aria-label=${label}
                              >
                                  <pf-tooltip position="top" part="copy-tooltip" content=${label}>
                                      ${this.copyIcon}
                                  </pf-tooltip>
                              </button>
                          `
                }
            </div>
            <div part="display">
                ${match(this.mode)
                    .with("json", json)
                    .with("yaml", yaml)
                    .with(
                        "tree",
                        () =>
                            html`<ak-structured-view
                                ?show-count=${this.showCount}
                                .value=${this.cleanedValue}
                            ></ak-structured-view>`,
                    )
                    .exhaustive()}
            </div>
        `;
    }
}
