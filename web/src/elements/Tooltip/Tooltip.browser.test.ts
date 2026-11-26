import "#elements/ak-tooltip";
import type { Tooltip } from "#elements/ak-tooltip";

import { afterEach, describe, expect, it, vi } from "vitest";

const mounted = new Set<HTMLElement>();

afterEach(() => {
    mounted.forEach((el) => el.remove());
    mounted.clear();
});

async function mount(placement: Tooltip["placement"]) {
    const wrapper = document.body.appendChild(document.createElement("div"));
    mounted.add(wrapper);
    wrapper.style.cssText = "padding: 200px; overflow: hidden;";

    const tooltip = document.createElement("ak-tooltip");
    tooltip.placement = placement;
    tooltip.innerHTML = `<button>Anchor</button><span slot="tooltip">Tip</span>`;
    wrapper.appendChild(tooltip);
    await tooltip.updateComplete;

    // Bypass the show delay; the state machine is not under test here.
    tooltip.expanded = true;
    await tooltip.updateComplete;
    // autoUpdate positions asynchronously.
    await new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 50)));

    const anchor = tooltip.querySelector("button")!.getBoundingClientRect();
    const floating = tooltip.shadowRoot!.querySelector<HTMLElement>('[part="tooltip"]')!;

    return { anchor, floating, rect: floating.getBoundingClientRect() };
}

const centerX = (r: DOMRect) => r.left + r.width / 2;

describe("ak-tooltip positioning", () => {
    it("centers a bottom tooltip just below its anchor", async () => {
        const { anchor, rect } = await mount("bottom");

        expect(Math.abs(centerX(rect) - centerX(anchor))).toBeLessThan(2);
        expect(rect.top).toBeGreaterThanOrEqual(anchor.bottom);
        expect(rect.top - anchor.bottom).toBeLessThan(16);
    });

    it("centers a top tooltip just above its anchor", async () => {
        const { anchor, rect } = await mount("top");

        expect(Math.abs(centerX(rect) - centerX(anchor))).toBeLessThan(2);
        expect(rect.bottom).toBeLessThanOrEqual(anchor.top);
        expect(anchor.top - rect.bottom).toBeLessThan(16);
    });

    it("uses the top layer when the Popover API exists", async () => {
        const { floating } = await mount("top");

        expect(floating.matches(":popover-open")).toBe("popover" in HTMLElement.prototype);
    });
});

async function mountMarkup(markup: string) {
    const wrapper = document.body.appendChild(document.createElement("div"));
    mounted.add(wrapper);
    wrapper.innerHTML = markup;

    const tooltip = wrapper.querySelector("ak-tooltip")!;
    await tooltip.updateComplete;
    // slotchange is dispatched as a microtask-queued event after assignment.
    await new Promise((resolve) => setTimeout(resolve));

    return { tooltip, anchor: wrapper.querySelector("button")! };
}

describe("ak-tooltip Escape", () => {
    const escape = () =>
        new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true });

    const markup = `<ak-tooltip><button>Edit</button><span slot="tooltip">Tip</span></ak-tooltip>`;

    it("dismisses a shown tooltip and consumes the key", async () => {
        const { tooltip } = await mountMarkup(markup);
        tooltip.dispatchEvent(new MouseEvent("mouseenter"));
        await new Promise((resolve) => setTimeout(resolve, tooltip.showDelay + 50));
        expect(tooltip.expanded).toBe(true);

        const outer = vi.fn();
        document.body.addEventListener("keydown", outer);

        const event = escape();
        document.body.dispatchEvent(event);
        await tooltip.updateComplete;

        expect(tooltip.expanded).toBe(false);
        expect(event.defaultPrevented).toBe(true);
        expect(outer).not.toHaveBeenCalled();
        document.body.removeEventListener("keydown", outer);
    });

    it("cancels a pending show", async () => {
        const { tooltip } = await mountMarkup(markup);

        tooltip.dispatchEvent(new MouseEvent("mouseenter"));
        document.body.dispatchEvent(escape());
        await new Promise((resolve) => setTimeout(resolve, tooltip.showDelay + 50));

        expect(tooltip.expanded).toBe(false);
    });

    it("leaves Escape alone when no tooltip is open", async () => {
        await mountMarkup(markup);

        const event = escape();
        document.body.dispatchEvent(event);

        expect(event.defaultPrevented).toBe(false);
    });
});

describe("ak-tooltip description", () => {
    it("describes the anchor with the slotted tooltip content", async () => {
        const { anchor } = await mountMarkup(
            `<ak-tooltip><button>Edit</button><span slot="tooltip">Edit this token</span></ak-tooltip>`,
        );

        const ids = anchor.getAttribute("aria-describedby")!.split(" ");

        expect(ids).toHaveLength(1);

        // Same tree as the anchor, so the IDREF resolves.
        expect(
            anchor.getRootNode() === document && document.getElementById(ids[0])?.textContent,
        ).toBe("Edit this token");
    });

    it("keeps existing describedby tokens and removes only its own on disconnect", async () => {
        const { tooltip, anchor } = await mountMarkup(
            `<span id="other">Other</span>
            <ak-tooltip><button aria-describedby="other">Edit</button><span slot="tooltip" id="tip">Tip</span></ak-tooltip>`,
        );

        expect(anchor.getAttribute("aria-describedby")).toBe("other tip");

        tooltip.remove();

        expect(anchor.getAttribute("aria-describedby")).toBe("other");
    });

    it("relinks when the tooltip content is replaced", async () => {
        const { tooltip, anchor } = await mountMarkup(
            `<ak-tooltip><button>Edit</button><span slot="tooltip" id="first">First</span></ak-tooltip>`,
        );

        tooltip
            .querySelector("#first")!
            .replaceWith(
                Object.assign(document.createElement("span"), { slot: "tooltip", id: "second" }),
            );

        await new Promise((resolve) => setTimeout(resolve));

        expect(anchor.getAttribute("aria-describedby")).toBe("second");
    });

    it("does not describe the anchor with content that already labels it", async () => {
        const { anchor } = await mountMarkup(
            `<ak-tooltip><button aria-labelledby="label"></button><span slot="tooltip" id="label">Switch view</span></ak-tooltip>`,
        );

        expect(anchor.hasAttribute("aria-describedby")).toBe(false);
        expect(anchor.getAttribute("aria-labelledby")).toBe("label");
    });

    it("falls back to aria-description for the deprecated content attribute", async () => {
        const { anchor } = await mountMarkup(
            `<ak-tooltip content="Legacy tip"><button>Edit</button></ak-tooltip>`,
        );

        expect(anchor.getAttribute("aria-description")).toBe("Legacy tip");
        expect(anchor.hasAttribute("aria-describedby")).toBe(false);
    });
});
