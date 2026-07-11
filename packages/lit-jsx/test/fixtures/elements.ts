import { html, LitElement } from "lit";

export class AkTestBadge extends LitElement {
    static properties = {
        label: { type: String },
        active: { type: Boolean },
        level: { type: String, attribute: "data-level" },
        items: { attribute: false },
    };

    declare label: string;
    declare active: boolean;
    declare level: string;
    declare items: string[];

    constructor() {
        super();
        this.label = "";
        this.active = false;
        this.level = "";
        this.items = [];
    }

    emitChange(): void {
        this.dispatchEvent(new CustomEvent("ak-change", { detail: { label: this.label } }));
    }

    render() {
        return html`<span data-testid="badge">${this.label}:${this.items.length}</span>`;
    }
}

customElements.define("ak-test-badge", AkTestBadge);

export class AkTestUnregistered extends LitElement {}

declare global {
    interface HTMLElementTagNameMap {
        "ak-test-badge": AkTestBadge;
    }
}
