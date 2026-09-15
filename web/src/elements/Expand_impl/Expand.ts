import "#elements/ExpansionToggle";

import Styles from "./Expand.styles";

import { AKElement } from "#elements/Base";
import { ExpansionToggle } from "#elements/ExpansionToggle";
import { type SlottedTemplateResult, type Spread } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { property, query } from "lit/decorators.js";

export class Expand extends AKElement {
    @property({ type: Boolean, reflect: true })
    public expanded = false;

    @property({ type: String, attribute: "text-open" })
    public textOpen = msg("Show less");

    @property({ type: String, attribute: "text-closed" })
    public textClosed = msg("Show more");

    static styles = [Styles];

    @query("ak-expansion-toggle")
    toggle!: ExpansionToggle;

    @query('[part="content"]')
    content!: HTMLDivElement;

    onToggle(ev: ToggleEvent) {
        this.expanded = ev.newState === "open";
    }

    render() {
        return html` <ak-expansion-toggle
                part="toggle"
                @toggle=${this.onToggle}
                ?expanded=${this.expanded}
                ><span part="toggle-text" slot="label"
                    >${this.expanded ? this.textOpen : this.textClosed}</span
                ></ak-expansion-toggle
            >
            <div part="content" ?hidden=${!this.expanded}>
                <slot></slot>
            </div>`;
    }

    protected override firstUpdated() {
        if (this.toggle && this.content) {
            this.toggle.controls = this.content;
        }
    }
}

export interface ExpandProps {
    expanded?: boolean;
    textOpen?: string;
    textClosed?: string;
}

export function akExpand(properties: ExpandProps, content: SlottedTemplateResult = nothing) {
    const message = typeof content === "string" ? html`<span>${content}</span>` : content;
    return html`<ak-expand ${spread(properties as Spread)}>${message}</ak-expand>`;
}
