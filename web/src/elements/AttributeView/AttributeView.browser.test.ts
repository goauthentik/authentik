import "#elements/ak-attribute-view";
import "#elements/messages/MessageContainer";
import { akAttributeView, type AkAttributeView } from "#elements/ak-attribute-view";
import type { StructuredView } from "#elements/ak-structured-view";

import { afterEach, describe, expect, it, vi } from "vitest";
import YAML from "yaml";

import { html, render, type TemplateResult } from "lit";

const mounted = new Set<HTMLElement>();

async function mountTemplate(template: TemplateResult): Promise<AkAttributeView> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);
    render(template, container);

    const element = container.querySelector("ak-attribute-view")!;
    await element.updateComplete;

    return element;
}

const mount = (value: unknown, mode = "json") =>
    mountTemplate(html`<ak-attribute-view mode=${mode} .value=${value}></ak-attribute-view>`);

const display = (element: AkAttributeView) =>
    element.renderRoot.querySelector<HTMLElement>('[part="display"]')!;

const copyButton = (element: AkAttributeView) =>
    element.renderRoot.querySelector<HTMLButtonElement>('[part="copy-button"]');

async function treeValue(element: AkAttributeView) {
    const tree = display(element).querySelector<StructuredView>("ak-structured-view")!;
    await tree.updateComplete;

    return tree.value;
}

/**
 * Stub the Clipboard API and return a function resolving to the text of the last write.
 *
 * `writeToClipboard` reports through `showMessage`, which needs an `#interface-root` and an
 * `ak-message-container`; the element under test stands in as the root.
 */
function stubClipboard(element: AkAttributeView) {
    element.id = "interface-root";
    mounted.add(document.body.appendChild(document.createElement("ak-message-container")));

    const write = vi.spyOn(navigator.clipboard, "write").mockResolvedValue(undefined);

    return async () => {
        const [items] = write.mock.lastCall ?? [[]];
        const blob = await items[0]?.getType("text/plain");

        return blob?.text();
    };
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
    vi.restoreAllMocks();
});

describe("ak-attribute-view: modes", () => {
    const value = { user: { name: "alice", groups: ["admins"] } };

    it("defaults to pretty-printed JSON", async () => {
        const element = await mountTemplate(
            html`<ak-attribute-view .value=${value}></ak-attribute-view>`,
        );

        expect(element.mode).toBe("json");

        expect(display(element).querySelector("pre")?.textContent).toBe(
            JSON.stringify(value, null, 2),
        );
    });

    it("renders YAML in yaml mode", async () => {
        const element = await mount(value, "yaml");

        expect(YAML.parse(display(element).querySelector("pre")!.textContent!)).toEqual(value);
    });

    it("renders an ak-structured-view in tree mode", async () => {
        const element = await mount(value, "tree");

        expect(display(element).querySelector("pre")).toBeNull();
        expect(await treeValue(element)).toEqual(value);
    });

    it("switches mode and reflects it when a toggle is clicked", async () => {
        const element = await mount(value);
        const group = element.renderRoot.querySelector("ak-toggle-group")!;
        await group.updateComplete;

        group.renderRoot.querySelector<HTMLButtonElement>('button[data-value="yaml"]')!.click();
        await element.updateComplete;

        expect(element.mode).toBe("yaml");
        expect(element.getAttribute("mode")).toBe("yaml");
        expect(YAML.parse(display(element).querySelector("pre")!.textContent!)).toEqual(value);
    });

    it("falls back to JSON for an unrecognized mode", async () => {
        const element = await mount(value);
        element.setAttribute("mode", "xml");

        await expect(element.updateComplete).resolves.toBe(true);
        expect(element.getAttribute("mode")).toBe("json");

        expect(display(element).querySelector("pre")?.textContent).toBe(
            JSON.stringify(value, null, 2),
        );
    });
});

describe("ak-attribute-view: value cleaning", () => {
    it("unescapes literal \\n sequences and escaped single quotes in strings", async () => {
        const element = await mount({ trace: "first\\nsecond", quote: "it\\'s" }, "tree");

        expect(await treeValue(element)).toEqual({ trace: "first\nsecond", quote: "it's" });
    });

    it("keeps arrays as arrays", async () => {
        const element = await mount({ list: ["a", "b"] }, "tree");
        const cleaned = (await treeValue(element)) as { list: unknown };

        expect(Array.isArray(cleaned.list)).toBe(true);
    });

    it("preserves numbers, booleans and null", async () => {
        const value = { count: 5, enabled: true, parent: null };
        const element = await mount(value);

        expect(JSON.parse(display(element).querySelector("pre")!.textContent!)).toEqual(value);
    });
});

describe("ak-attribute-view: copy", () => {
    it("copies the value as JSON in json mode", async () => {
        const element = await mount({ a: "1" });
        const lastWrite = stubClipboard(element);

        copyButton(element)!.click();

        await expect.poll(lastWrite).toBe(JSON.stringify({ a: "1" }, null, 2));
    });

    it("copies the value as YAML in yaml mode", async () => {
        const element = await mount({ a: "1" }, "yaml");
        const lastWrite = stubClipboard(element);

        copyButton(element)!.click();

        await expect.poll(lastWrite).toBe(YAML.stringify({ a: "1" }));
    });

    it.each(["json", "yaml"])(
        "copies the original value, not the display-cleaned one, in %s mode",
        async (mode) => {
            const value = { pattern: "^a\\nb$", quote: "it\\'s" };
            const element = await mount(value, mode);
            const lastWrite = stubClipboard(element);

            copyButton(element)!.click();

            await expect
                .poll(lastWrite)
                .toBe(mode === "yaml" ? YAML.stringify(value) : JSON.stringify(value, null, 2));

            // The display still shows the cleaned value.
            expect(element.cleanedValue).toEqual({ pattern: "^a\nb$", quote: "it's" });
        },
    );

    it("styles the copy button as a PatternFly plain button", async () => {
        const element = await mount({});
        const style = getComputedStyle(copyButton(element)!);

        // Without the PatternFly button sheet, the user agent's 2px button border survives.
        expect(style.borderTopWidth).toBe("0px");
    });

    it("labels the copy button for the active format", async () => {
        const element = await mount({}, "yaml");

        expect(copyButton(element)?.getAttribute("aria-label")).toBe("Copy YAML to clipboard");
    });

    it("omits the copy button when hide-copy is set", async () => {
        const element = await mountTemplate(
            html`<ak-attribute-view hide-copy .value=${{}}></ak-attribute-view>`,
        );

        expect(copyButton(element)).toBeNull();
    });
});

describe("akAttributeView builder", () => {
    it("passes value, mode and hideCopy through to the element", async () => {
        const value = { a: "1" };

        const element = await mountTemplate(
            akAttributeView({ value, mode: "yaml", hideCopy: true, id: "built" }),
        );

        expect(element.value).toBe(value);
        expect(element.mode).toBe("yaml");
        expect(element.hideCopy).toBe(true);
        expect(element.id).toBe("built");
    });

    it("keeps the component defaults when options are omitted", async () => {
        const element = await mountTemplate(akAttributeView({ value: {} }));

        expect(element.mode).toBe("json");
        expect(element.hideCopy).toBe(false);
    });
});
