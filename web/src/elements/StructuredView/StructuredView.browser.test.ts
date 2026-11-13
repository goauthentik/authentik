import "#elements/ak-structured-view";
import { akStructuredView, type StructuredView } from "#elements/ak-structured-view";
import type { JsonValue } from "#elements/StructuredView/StructuredView.component";

import { afterEach, describe, expect, it } from "vitest";
import { userEvent } from "vitest/browser";

import { html, render, type TemplateResult } from "lit";

const mounted = new Set<HTMLElement>();

async function mountTemplate(template: TemplateResult): Promise<StructuredView> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);
    render(template, container);

    const element = container.querySelector("ak-structured-view")!;
    await element.updateComplete;

    return element;
}

const mount = (value: JsonValue) =>
    mountTemplate(html`<ak-structured-view .value=${value}></ak-structured-view>`);

const normalize = (s: string | null | undefined) => (s ?? "").replace(/\s+/g, " ").trim();

const item = (element: StructuredView, path: string) =>
    element.renderRoot.querySelector<HTMLElement>(`[part="tree-item"][data-path="${path}"]`);

const branch = (element: StructuredView, path: string) =>
    item(element, path)?.querySelector<HTMLDetailsElement>(":scope > details") ?? null;

const key = (element: StructuredView, path: string) =>
    item(element, path)?.querySelector<HTMLElement>(
        ':scope > [part="tree-key"], :scope > details > [part="tree-key"]',
    ) ?? null;

const summary = (element: StructuredView, path: string) =>
    normalize(key(element, path)?.querySelector('[part="summary"]')?.textContent);

/**
 * Click a branch's summary. `<details>` dispatches `toggle` asynchronously, so wait for it.
 */
async function toggle(element: StructuredView, path: string) {
    const toggled = new Promise((resolve) =>
        branch(element, path)!.addEventListener("toggle", resolve, { once: true }),
    );

    key(element, path)!.click();
    await toggled;
    await element.updateComplete;
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-structured-view: rendering", () => {
    it("renders a root string as a single line", async () => {
        const element = await mount("hello");
        const line = element.renderRoot.querySelector('[part="oneline-string"]');

        expect(normalize(line?.textContent)).toBe("hello");
    });

    it("renders one tree item per object key", async () => {
        const element = await mount({ name: "alice", role: "admin" });
        const paths = [...element.renderRoot.querySelectorAll<HTMLElement>('[part="tree-item"]')];

        expect(paths.map((el) => el.dataset.path)).toEqual(["name", "role"]);
        expect(normalize(item(element, "name")?.textContent)).toBe("name: alice");
    });

    it("renders strings containing newlines as preformatted blocks", async () => {
        const element = await mount({ trace: "line one\nline two" });
        const pre = item(element, "trace")?.querySelector('[part="multiline-string"]');

        expect(pre).not.toBeNull();
        expect(pre?.textContent).toContain("line one");
        expect(pre?.textContent).toContain("line two");
    });

    it("wraps long single-line strings instead of overflowing", async () => {
        const long = "x".repeat(400);

        const element = await mountTemplate(
            html`<ak-structured-view style="width: 200px" .value=${{ long }}></ak-structured-view>`,
        );

        const line = item(element, "long")?.querySelector<HTMLElement>('[part="oneline-string"]');

        expect(line).not.toBeNull();
        expect(line!.getClientRects().length).toBeGreaterThan(1);
        expect(element.scrollWidth).toBeLessThanOrEqual(element.clientWidth);
    });

    it("wraps long lines inside multiline strings instead of overflowing", async () => {
        const element = await mountTemplate(
            html`<ak-structured-view
                style="width: 200px"
                .value=${{ trace: `short\n${"y".repeat(400)}` }}
            ></ak-structured-view>`,
        );

        expect(item(element, "trace")?.querySelector('[part="multiline-string"]')).not.toBeNull();
        expect(element.scrollWidth).toBeLessThanOrEqual(element.clientWidth);
    });

    it("re-renders when the value is replaced", async () => {
        const element = await mount({ a: "1" });
        element.value = { b: "2" };
        await element.updateComplete;

        expect(item(element, "a")).toBeNull();
        expect(item(element, "b")).not.toBeNull();
    });

    it("renders numbers, booleans and null without quotation marks", async () => {
        const element = await mount({ n: 5, ok: true, none: null });

        expect(normalize(item(element, "n")?.textContent)).toBe("n: 5");
        expect(normalize(item(element, "ok")?.textContent)).toBe("ok: true");
        expect(normalize(item(element, "none")?.textContent)).toBe("none: null");
    });
});

describe("ak-structured-view: expansion", () => {
    it("starts with branches collapsed", async () => {
        const element = await mount({ nested: { a: "1" } });

        expect(branch(element, "nested")?.open).toBe(false);
        expect(item(element, "nested.a")).toBeNull();
    });

    it("expands and collapses a branch when its key is clicked", async () => {
        const element = await mount({ nested: { a: "1" } });

        await toggle(element, "nested");
        expect(branch(element, "nested")?.open).toBe(true);
        expect(item(element, "nested.a")).not.toBeNull();

        await toggle(element, "nested");
        expect(branch(element, "nested")?.open).toBe(false);
        expect(item(element, "nested.a")).toBeNull();
    });

    it("expands sibling branches independently", async () => {
        const element = await mount({ left: { a: "1" }, right: { b: "2" } });

        await toggle(element, "left");

        expect(item(element, "left.a")).not.toBeNull();
        expect(item(element, "right.b")).toBeNull();
    });

    it("starts collapsed again when the value is replaced", async () => {
        const element = await mount({ nested: { a: "1" } });

        await toggle(element, "nested");
        element.value = { nested: { a: "2" } };
        await element.updateComplete;

        expect(branch(element, "nested")?.open).toBe(false);
    });

    it("uses array indices as paths", async () => {
        const element = await mount({ list: [{ id: "x" }, { id: "y" }] });

        await toggle(element, "list");
        await toggle(element, "list.1");

        expect(item(element, "list.0.id")).toBeNull();
        expect(normalize(item(element, "list.1.id")?.textContent)).toBe("id: y");
    });

    it("keeps a dotted key separate from a nested path of the same spelling", async () => {
        const element = await mount({ "a.b": { x: "1" }, "a": { b: { y: "2" } } });

        await toggle(element, "a");
        await toggle(element, "a.b"); // The top-level "a.b" key is rendered first.

        expect(item(element, "a.b.y")).toBeNull();
    });
});

describe("ak-structured-view: summaries", () => {
    it("shows a summary only while a branch is collapsed", async () => {
        const element = await mount({ nested: { a: "1" } });

        expect(summary(element, "nested")).not.toBe("");

        await toggle(element, "nested");
        expect(summary(element, "nested")).toBe("");
    });

    it("marks an object with more keys than summary-maxcount as truncated", async () => {
        const element = await mountTemplate(
            html`<ak-structured-view
                summary-maxcount="1"
                .value=${{ nested: { a: "1", b: "2" } }}
            ></ak-structured-view>`,
        );

        expect(summary(element, "nested")).toContain("…");
        expect(summary(element, "nested")).not.toContain("b:");
    });

    it("summarizes each child by its own value", async () => {
        const element = await mount({ nested: { a: 1, b: "two" } });

        expect(summary(element, "nested")).toBe('{ a: 1, b: "two" }');
    });

    it("does not emit a separator after the last entry", async () => {
        const element = await mount({ nested: { a: {} } });

        expect(summary(element, "nested")).not.toMatch(/,\s*}$/);
    });

    it("truncates long strings to summary-maxlength", async () => {
        const element = await mountTemplate(
            html`<ak-structured-view
                summary-maxlength="5"
                .value=${{ nested: { s: "abcdefghij" } }}
            ></ak-structured-view>`,
        );

        expect(summary(element, "nested")).toContain('"abcde…"');
    });
});

describe("ak-structured-view: summary spacing", () => {
    /**
     * Mount in a plain monospace font with the word-spacing token set, so widths divide into
     * whole characters.
     */
    const mountSpaced = (value: JsonValue) =>
        mountTemplate(html`<ak-structured-view
            style="font-family: monospace; --ak-c-structured-view__summary--WordSpacing: -0.5ch"
            .value=${value}
        ></ak-structured-view>`);

    const widthInCh = (element: StructuredView, selector: string) => {
        const target = element.renderRoot.querySelector<HTMLElement>(selector)!;
        const probe = target.appendChild(document.createElement("span"));
        probe.style.cssText = "position: absolute; width: 1ch";
        const ch = probe.getBoundingClientRect().width;
        probe.remove();

        return target.getBoundingClientRect().width / ch;
    };

    function selectedText(node: Node) {
        const selection = getSelection()!;
        const range = document.createRange();
        range.selectNodeContents(node);
        selection.removeAllRanges();
        selection.addRange(range);
        const text = selection.toString();
        selection.removeAllRanges();

        return text;
    }

    it("narrows the spaces between summary tokens", async () => {
        const element = await mountSpaced({ nested: { a: 1 } });

        // "{ a: 1 }" is 8 characters, 3 of them spaces narrowed to 0.5ch each.
        expect(widthInCh(element, '[part="summary"]')).toBeCloseTo(6.5, 1);
    });

    it("keeps normal spacing inside summarized keys and strings", async () => {
        const element = await mountSpaced({ nested: { "first name": "a b" } });

        expect(widthInCh(element, '[part="summary-key"]')).toBeCloseTo("first name:".length, 1);
        expect(widthInCh(element, '[part="summary-string"]')).toBeCloseTo('"a b"'.length, 1);
    });

    it("copies a summary with ordinary spaces", async () => {
        const element = await mountSpaced({ nested: { a: 1, b: "two" } });
        const target = element.renderRoot.querySelector('[part="summary"]')!;

        expect(selectedText(target)).toBe('{ a: 1, b: "two" }');
    });

    it("copies a leaf row with a space after the key", async () => {
        const element = await mountSpaced({ name: "alice" });

        expect(selectedText(item(element, "name")!).trim()).toBe("name: alice");
    });
});

describe("ak-structured-view: accessibility", () => {
    it("does not give the host an ARIA role", async () => {
        const element = await mount({ a: "1" });

        expect(element.hasAttribute("role")).toBe(false);
    });

    it("renders branches as native disclosure widgets", async () => {
        const element = await mount({ nested: { a: "1" } });

        expect(key(element, "nested")?.localName).toBe("summary");
    });

    it("omits disclosure semantics from leaf items", async () => {
        const element = await mount({ leaf: "1" });

        expect(branch(element, "leaf")).toBeNull();
        expect(item(element, "leaf")?.querySelector("[aria-expanded]")).toBeNull();
    });

    it("expands and collapses a branch from the keyboard", async () => {
        const element = await mount({ nested: { a: "1" } });
        const target = key(element, "nested")!;

        target.focus();
        expect(element.shadowRoot!.activeElement).toBe(target);

        await userEvent.keyboard("{Enter}");
        await expect.poll(() => item(element, "nested.a")).not.toBeNull();

        await userEvent.keyboard("[Space]");
        await expect.poll(() => item(element, "nested.a")).toBeNull();
    });
});

describe("ak-structured-view: show-count", () => {
    const countOf = (element: StructuredView, path: string) =>
        item(element, path)?.querySelector(':scope > details > summary [part="keycount"]') ?? null;

    const mountCounted = (value: JsonValue) =>
        mountTemplate(html`<ak-structured-view show-count .value=${value}></ak-structured-view>`);

    it("hides counts by default", async () => {
        const element = await mount({ nested: { a: "1", b: "2" } });

        expect(countOf(element, "nested")).toBeNull();
    });

    it.each([
        [{ a: "1" }, "(1 key)"],
        [{ a: "1", b: "2", c: "3", d: "4" }, "(4 keys)"],
        [["a"], "(1 item)"],
        [["a", "b"], "(2 items)"],
    ])("counts every entry of %j, including ones the summary hides", async (nested, expected) => {
        const element = await mountCounted({ nested });

        expect(normalize(countOf(element, "nested")?.textContent)).toBe(expected);
    });

    it.each([[{}], [[]]])("omits the count for the empty container %j", async (nested) => {
        const element = await mountCounted({ nested });

        expect(countOf(element, "nested")).toBeNull();
    });

    it("drops the count with the summary once a branch is opened", async () => {
        const element = await mountCounted({ nested: { a: "1" } });

        await toggle(element, "nested");

        expect(countOf(element, "nested")).toBeNull();
    });
});

describe("akStructuredView builder", () => {
    it("passes the value as a property and the summary limits as attributes", async () => {
        const value = { nested: { a: "1" } };

        const element = await mountTemplate(
            akStructuredView({ value, summaryMaxLength: 7, summaryMaxCount: 2, id: "built" }),
        );

        expect(element.value).toBe(value);
        expect(element.length).toBe(7);
        expect(element.count).toBe(2);
        expect(element.id).toBe("built");
    });

    it("keeps the component defaults when limits are omitted", async () => {
        const element = await mountTemplate(akStructuredView({ value: {} }));

        expect(element.length).toBe(15);
        expect(element.count).toBe(3);
        expect(element.showCount).toBe(false);
    });

    it("sets show-count from showCount", async () => {
        const element = await mountTemplate(
            akStructuredView({ value: { nested: { a: "1" } }, showCount: true }),
        );

        expect(element.showCount).toBe(true);
        expect(element.hasAttribute("show-count")).toBe(true);
    });
});
