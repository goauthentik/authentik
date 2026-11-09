import "#elements/ak-tree-view";
import { akTreeView, type TreeView } from "#elements/ak-tree-view";
import type { JsonValue } from "#elements/TreeView/TreeView.component";

import { afterEach, describe, expect, it } from "vitest";

import { html, render, type TemplateResult } from "lit";

const mounted = new Set<HTMLElement>();

async function mountTemplate(template: TemplateResult): Promise<TreeView> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);
    render(template, container);

    const element = container.querySelector("ak-tree-view")!;
    await element.updateComplete;

    return element;
}

const mount = (value: JsonValue) =>
    mountTemplate(html`<ak-tree-view .value=${value}></ak-tree-view>`);

const normalize = (s: string | null | undefined) => (s ?? "").replace(/\s+/g, " ").trim();

const item = (element: TreeView, path: string) =>
    element.renderRoot.querySelector<HTMLElement>(`[part="tree-item"][data-path="${path}"]`);

const key = (element: TreeView, path: string) =>
    item(element, path)?.querySelector<HTMLElement>(':scope > [part="tree-key"]') ?? null;

const summary = (element: TreeView, path: string) =>
    normalize(key(element, path)?.querySelector('[part="summary"]')?.textContent);

async function toggle(element: TreeView, path: string) {
    key(element, path)!.click();
    await element.updateComplete;
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-tree-view: rendering", () => {
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

describe("ak-tree-view: expansion", () => {
    it("starts with branches collapsed", async () => {
        const element = await mount({ nested: { a: "1" } });

        expect(item(element, "nested")?.getAttribute("aria-expanded")).toBe("false");
        expect(item(element, "nested.a")).toBeNull();
    });

    it("expands and collapses a branch when its key is clicked", async () => {
        const element = await mount({ nested: { a: "1" } });

        await toggle(element, "nested");
        expect(item(element, "nested")?.getAttribute("aria-expanded")).toBe("true");
        expect(item(element, "nested.a")).not.toBeNull();

        await toggle(element, "nested");
        expect(item(element, "nested")?.getAttribute("aria-expanded")).toBe("false");
        expect(item(element, "nested.a")).toBeNull();
    });

    it("expands sibling branches independently", async () => {
        const element = await mount({ left: { a: "1" }, right: { b: "2" } });

        await toggle(element, "left");

        expect(item(element, "left.a")).not.toBeNull();
        expect(item(element, "right.b")).toBeNull();
    });

    it("uses array indices as paths", async () => {
        const element = await mount({ list: [{ id: "x" }, { id: "y" }] });

        await toggle(element, "list");
        await toggle(element, "list.1");

        expect(item(element, "list.0.id")).toBeNull();
        expect(normalize(item(element, "list.1.id")?.textContent)).toBe("id: y");
    });

    // Defect: paths are joined with ".", so a key that itself contains "." shares state with a
    // nested path of the same spelling.
    it.fails("keeps a dotted key separate from a nested path of the same spelling", async () => {
        const element = await mount({ "a.b": { x: "1" }, "a": { b: { y: "2" } } });

        await toggle(element, "a");
        await toggle(element, "a.b"); // The top-level "a.b" key is rendered first.

        expect(item(element, "a.b.y")).toBeNull();
    });
});

describe("ak-tree-view: summaries", () => {
    it("shows a summary only while a branch is collapsed", async () => {
        const element = await mount({ nested: { a: "1" } });

        expect(summary(element, "nested")).not.toBe("");

        await toggle(element, "nested");
        expect(summary(element, "nested")).toBe("");
    });

    it("marks an object with more keys than summary-maxcount as truncated", async () => {
        const element = await mountTemplate(
            html`<ak-tree-view
                summary-maxcount="1"
                .value=${{ nested: { a: "1", b: "2" } }}
            ></ak-tree-view>`,
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
            html`<ak-tree-view
                summary-maxlength="5"
                .value=${{ nested: { s: "abcdefghij" } }}
            ></ak-tree-view>`,
        );

        expect(summary(element, "nested")).toContain('"abcde…"');
    });
});

describe("ak-tree-view: accessibility", () => {
    // Defect: the host is given `role="node"`, which is not an ARIA role.
    it.fails("exposes the tree role on the host", async () => {
        const element = await mount({ a: "1" });

        expect(element.getAttribute("role")).toBe("tree");
    });

    // Defect: leaf items are rendered with `aria-expanded="false"`, which announces them as
    // collapsed branches.
    it.fails("omits aria-expanded from leaf items", async () => {
        const element = await mount({ leaf: "1" });

        expect(item(element, "leaf")?.hasAttribute("aria-expanded")).toBe(false);
    });

    // Defect: the toggle is a click handler on a <span>; it is not focusable and has no keyboard
    // handling.
    it.fails("expands a branch from the keyboard", async () => {
        const element = await mount({ nested: { a: "1" } });
        const target = key(element, "nested")!;

        expect(target.tabIndex).toBeGreaterThanOrEqual(0);

        target.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
        await element.updateComplete;

        expect(item(element, "nested.a")).not.toBeNull();
    });
});

describe("akTreeView builder", () => {
    it("passes the value as a property and the summary limits as attributes", async () => {
        const value = { nested: { a: "1" } };

        const element = await mountTemplate(
            akTreeView({ value, summaryMaxLength: 7, summaryMaxCount: 2, id: "built" }),
        );

        expect(element.value).toBe(value);
        expect(element.length).toBe(7);
        expect(element.count).toBe(2);
        expect(element.id).toBe("built");
    });

    it("keeps the component defaults when limits are omitted", async () => {
        const element = await mountTemplate(akTreeView({ value: {} }));

        expect(element.length).toBe(15);
        expect(element.count).toBe(3);
    });
});
