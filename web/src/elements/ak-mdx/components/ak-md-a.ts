import { AKElement } from "#elements/Base";

import { css, PropertyValues } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-md-a")
export class AKMarkdownAnchor extends AKElement {
    public static styles = [
        css`
            :host {
                display: contents;
            }
        `,
    ];

    protected defaultSlot: HTMLSlotElement = this.ownerDocument.createElement("slot");

    protected override render() {
        return this.defaultSlot;
    }

    protected override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        const anchors = this.defaultSlot
            .assignedElements({ flatten: true })
            .filter((element) => element.matches("a"));

        for (const anchor of anchors) {
            anchor.addEventListener("click", this.clickListener);
        }
    }

    protected clickListener(event: MouseEvent): void {
        const anchor = event.currentTarget as HTMLAnchorElement;
        const href = anchor.getAttribute("href");

        if (!href || !href.startsWith("#")) return;

        event.preventDefault();

        const rootNode = anchor.getRootNode() as ShadowRoot;

        const elementID = href.slice(1);
        const target = rootNode.getElementById(elementID);

        if (!target) {
            console.warn(`Element with ID ${elementID} not found`);
            return;
        }

        target.scrollIntoView({
            behavior: "smooth",
            block: "center",
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-md-a": AKMarkdownAnchor;
    }
}
