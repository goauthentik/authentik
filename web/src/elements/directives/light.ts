import { render, TemplateResult } from "lit";
import { AsyncDirective } from "lit/async-directive.js";
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
    #rootPart: RootPart | null = null;
    #sentinel: Comment | null = null;

    constructor(partInfo: PartInfo) {
        super(partInfo);
        if (partInfo.type !== PartType.CHILD) {
            throw new Error("The `light()` directive can only be use in child position");
        }
    }

    render(_template?: TemplateResult, options?: LightChildOptions) {
        this.#slotName ??= options?.slotName ?? `lc-${Math.random().toString(36).slice(2, 8)}`;
        // The lack of `html` here is deliberate. This code only runs in SSR mode. We don't use in in
        // the `update()` phase.
        return `<slot name="${this.#slotName}"></slot>`;
    }

    #withSplicedSlotname(template: TemplateResult): TemplateResult {
        const raw = template.strings.raw;
        const strings = [...(template.strings as unknown as string[])];
        const values = [...template.values];
        strings.splice(1, 0, " slot=");
        values.splice(1, 0, this.#slotName);
        // @ts-expect-error This is esoteric coercion.
        (strings as TemplateStringsArray).raw = raw;
        return {
            ...template,
            strings: Object.freeze(strings as unknown as TemplateStringsArray),
            values: values,
        };
    }

    update(part: ChildPart, [template, options = {}]: [TemplateResult, LightChildOptions]) {
        if (!/^\s*</.test(template.strings[0])) {
            throw new Error("The `light()` directive can only take an ElementNode, not a TextNode");
        }

        this.#slotName ??= options?.slotName ?? `lc-${Math.random().toString(36).slice(2, 8)}`;

        // This places a comment in the LightDom that belongs to this directive. Comments are not
        // part of the DOM tree for the purposes of CSS, so it will be possible to style this child
        // directly without a wrapper.

        if (!this.#sentinel) {
            const host = (part.options?.host ||
                (part.parentNode.getRootNode() as ShadowRoot).host) as Element;
            this.#sentinel = document.createComment("");
            host.appendChild(this.#sentinel);
        }

        const slottedTemplate = template.strings.find((s) => /slot=["']$/.test(s))
            ? template
            : this.#withSplicedSlotname(template);

        if (!this.#sentinel.parentNode) {
            throw new Error("Could not assign sentinel to element.");
        }

        const renderOptions = Object.fromEntries(
            Object.entries(options).filter(([key]) => ["host"].includes(key)),
        );

        this.#rootPart = render(slottedTemplate, this.#sentinel.parentNode as HTMLElement, {
            renderBefore: this.#sentinel,
            ...renderOptions,
        });

        return (this.#slot ??= Object.assign(document.createElement("slot"), {
            name: this.#slotName,
        }));
    }

    disconnected() {
        this.#rootPart?.setConnected(false);
    }

    reconnected() {
        this.#rootPart?.setConnected(true);
    }
}

export const light = directive(LightChildDirective);
