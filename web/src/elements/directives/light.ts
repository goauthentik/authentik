import { html, nothing, render, TemplateResult } from "lit";
import { AsyncDirective, DirectiveResult } from "lit/async-directive.js";
import { ChildPart, directive, PartInfo, PartType } from "lit/directive.js";
import { RootPart } from "lit/html.js";

export interface LightChildOptions {
    // Optional alternative target for any `@event`-style handlers passed into the template. NOTE:
    // this only works if the handlers do not already have a `this` bound to them, so only ordinary
    // functions and methods will respond to this parameter; arrow function class fields and bound
    // functions will use the `this` to which they were bound.

    host?: Element;
    slotName?: string;
}

class LightChildDirective extends AsyncDirective {
    #slotName: string | null = null;
    #slot: HTMLSlotElement | null = null;
    #host: Element | null = null;
    #rootPart: RootPart | null = null;
    #sentinel: Comment | null = null;

    constructor(partInfo: PartInfo) {
        super(partInfo);
        if (partInfo.type !== PartType.CHILD) {
            throw new Error("The `light()` directive can only be use in child position");
        }
    }

    render(_template?: TemplateResult | DirectiveResult, options?: LightChildOptions) {
        this.#slotName ??= options?.slotName ?? `lc-${Math.random().toString(36).slice(2, 8)}`;
        return html`<slot name="${this.#slotName}"></slot>`;
    }

    update(
        part: ChildPart,
        [template, options = {}]: [TemplateResult | DirectiveResult, LightChildOptions],
    ) {
        this.#slotName ??= options?.slotName ?? `lc-${Math.random().toString(36).slice(2, 8)}`;

        // This places a comment in the LightDom that belongs to this directive. Comments are not
        // part of the DOM tree for the purposes of CSS, so it will be possible to style this child
        // directly without a wrapper.

        if (!this.#sentinel) {
            const rootNode = part.parentNode.getRootNode();
            this.#host ??= (part.options?.host ||
                (rootNode instanceof ShadowRoot ? rootNode.host : null)) as Element | null;

            if (!this.#host) {
                throw new Error(
                    "light() must be used inside a shadow root or a valid options.host",
                );
            }

            this.#sentinel = document.createComment("");
            this.#host.appendChild(this.#sentinel);
        }

        if (!this.#sentinel.parentNode) {
            throw new Error("Could not assign sentinel to element.");
        }

        const renderOptions = Object.fromEntries(
            Object.entries(options).filter(([key]) => ["host"].includes(key)),
        );

        this.#rootPart = render(template, this.#sentinel.parentNode as HTMLElement, {
            renderBefore: this.#sentinel,
            ...renderOptions,
        });

        const rendered = this.#sentinel.previousSibling;
        if (rendered instanceof Element) {
            rendered.slot = this.#slotName;
        }

        return (this.#slot ??= Object.assign(document.createElement("slot"), {
            name: this.#slotName,
        }));
    }

    disconnected() {
        if (this.#sentinel?.parentNode && this.#host?.isConnected) {
            // The content being rendered this way, with the `render()` *function*, has its own Lit
            // VDOM comment nodes in the HTML are unrelated to the `host` context. Rendering
            // `nothing` here ensures that any children of the lightDOM component receive clean-up
            // signals and correctly disconnect (including listeners, etc.) from the current display
            // as well. This is what lets us receive other DirectiveResults as template content.

            render(nothing, this.#sentinel.parentNode as HTMLElement, {
                renderBefore: this.#sentinel,
            });
        }
        this.#rootPart?.setConnected(false);
    }

    reconnected() {
        this.#rootPart?.setConnected(true);
    }
}

export const light = directive(LightChildDirective);
