import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";

type Mode = "tree" | "json" | "yaml";

@customElement("ak-attributes")
export class AkDataView extends LitElement {
    @property({ attribute: false }) value: unknown;
    @state() private mode: Mode = "tree";

    // Light DOM, per your slot-heavy architecture — password managers,
    // browser automation, and test tooling all need to see into this.
    createRenderRoot() {
        return this;
    }

    static styles = css``;

    private typeOf(v: unknown) {
        if (v === null) return "null";
        if (Array.isArray(v)) return "array";
        return typeof v;
    }

    private renderTree(obj: unknown, depth = 0) {
        const isArr = Array.isArray(obj);
        const entries: [string, unknown][] = isArr
            ? (obj as unknown[]).map((v, i) => [String(i), v])
            : Object.entries(obj as Record<string, unknown>);

        return html`
            <div class=${depth > 0 ? "nested" : ""}>
                ${entries.map(([key, val]) => {
                    const t = this.typeOf(val);
                    if (t === "object" || t === "array") {
                        const count =
                            t === "array"
                                ? (val as unknown[]).length
                                : Object.keys(val as object).length;
                        return html`
                            <div class="row">
                                ${!isArr ? html`<span class="key">${key}</span>` : ""}
                                <span class="hint"
                                    >${t === "array"
                                        ? `${count} item${count === 1 ? "" : "s"}`
                                        : ""}</span
                                >
                            </div>
                            ${this.renderTree(val, depth + 1)}
                        `;
                    }
                    const valClass =
                        {
                            string: "val-string",
                            number: "val-number",
                            boolean: "val-bool",
                            null: "val-null",
                        }[t] ?? "";
                    return html`
                        <div class="row">
                            ${!isArr ? html`<span class="key">${key}</span>` : ""}
                            <span class=${valClass}>${t === "null" ? "null" : String(val)}</span>
                        </div>
                    `;
                })}
            </div>
        `;
    }

    private async copy(text: string) {
        await navigator.clipboard.writeText(text);
    }

    render() {
        const json = JSON.stringify(this.value, null, 2);
        const yaml = toYaml(this.value);
        return html`
            <div role="tablist">
                ${(["tree", "json", "yaml"] as Mode[]).map(
                    (m) =>
                        html`<button
                            role="tab"
                            aria-selected=${this.mode === m}
                            @click=${() => (this.mode = m)}
                        >
                            ${m}
                        </button>`
                )}
            </div>
            ${this.mode === "tree"
                ? this.renderTree(this.value)
                : html`
                      <div style="position: relative;">
                          <button @click=${() => this.copy(this.mode === "json" ? json : yaml)}>
                              Copy
                          </button>
                          <pre>${this.mode === "json" ? json : yaml}</pre>
                      </div>
                  `}
        `;
    }
}
