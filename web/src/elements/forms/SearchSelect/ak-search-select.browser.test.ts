import "./ak-search-select.js";
import { SearchSelect } from "./ak-search-select.js";
import { SearchSelectActionEvent, SearchSelectChangeEvent } from "./events.js";
import type { SearchSelectSource } from "./shared.js";

import { userEvent } from "@vitest/browser/context";
import { afterEach, describe, expect, it, vi } from "vitest";

interface Item {
    pk: string;
    name: string;
    slug: string;
}

const firstPage: Item[] = [
    { pk: "1", name: "Alpha", slug: "alpha" },
    { pk: "2", name: "Bravo", slug: "bravo" },
    { pk: "3", name: "Charlie", slug: "charlie" },
];

const offPageItem: Item = { pk: "99", name: "Zulu", slug: "zulu" };

function createSource(overrides: Partial<SearchSelectSource<Item>> = {}): SearchSelectSource<Item> {
    return {
        fetchObjects: vi.fn(async (query?: string) =>
            query ? firstPage.filter((item) => item.name.toLowerCase().includes(query)) : firstPage,
        ),
        keyOf: (item) => item.pk,
        labelOf: (item) => item.name,
        describe: (item) => item.slug,
        ...overrides,
    };
}

const mounted = new Set<HTMLElement>();

interface MountInit {
    source?: SearchSelectSource<Item>;
    value?: string;
    selectedObject?: Item | null;
    required?: boolean;
    blankable?: boolean;
    actionLabel?: string;
}

async function mount(
    init: MountInit = {},
): Promise<{ form: HTMLFormElement; element: SearchSelect<Item> }> {
    const form = document.body.appendChild(document.createElement("form"));
    mounted.add(form);

    const element = new SearchSelect<Item>();

    element.name = "item";
    element.source = init.source ?? createSource();
    element.value = init.value ?? "";
    element.selectedObject = init.selectedObject ?? null;
    element.required = init.required ?? false;
    element.blankable = init.blankable ?? false;
    element.actionLabel = init.actionLabel ?? null;

    form.appendChild(element);

    await element.settled;

    return { form, element };
}

function input(element: SearchSelect<Item>): HTMLInputElement {
    return element.renderRoot.querySelector("input")!;
}

function optionLabels(element: SearchSelect<Item>): string[] {
    return Array.from(
        element.renderRoot.querySelectorAll(".ak-c-search-select__option-label"),
        (label) => label.textContent!.trim(),
    );
}

function key(element: SearchSelect<Item>, name: string): void {
    input(element).dispatchEvent(new KeyboardEvent("keydown", { key: name, bubbles: true }));
}

async function type(element: SearchSelect<Item>, text: string): Promise<void> {
    input(element).value = text;
    input(element).dispatchEvent(new InputEvent("input", { bubbles: true }));

    await element.settled;
}

afterEach(() => {
    for (const container of mounted) container.remove();
    mounted.clear();
});

describe("ak-search-select", () => {
    it("fetches once when connected", async () => {
        const source = createSource();

        await mount({ source });

        expect(source.fetchObjects, "One fetch for the first page").toHaveBeenCalledOnce();
    });

    it("labels a value that is not on the fetched page", async () => {
        const { element } = await mount({ value: offPageItem.pk, selectedObject: offPageItem });

        expect(input(element).value, "Input shows the label").toBe("Zulu");

        expect(optionLabels(element), "Selection is listed ahead of the page").toEqual([
            "Zulu",
            "Alpha",
            "Bravo",
            "Charlie",
        ]);
    });

    it("resolves the selected object from the fetched page when given only a value", async () => {
        const { element } = await mount({ value: "2" });

        expect(element.selectedObject, "Object is resolved by key").toEqual(firstPage[1]);
        expect(input(element).value, "Input shows the label").toBe("Bravo");
    });

    it("preselects a default when it has no value", async () => {
        const changes: Array<Item | null> = [];

        const source = createSource({
            preselect: (objects) => objects.find((item) => item.slug === "charlie"),
        });

        const form = document.body.appendChild(document.createElement("form"));
        mounted.add(form);

        const element = new SearchSelect<Item>();
        element.name = "item";
        element.source = source;

        element.addEventListener(SearchSelectChangeEvent.eventName, (event) => {
            changes.push((event as SearchSelectChangeEvent<Item>).detail.value);
        });

        form.appendChild(element);
        await element.settled;

        expect(element.value, "Default's key becomes the value").toBe("3");
        expect(new FormData(form).get("item"), "Form sees the value").toBe("3");
        expect(changes, "A change is announced").toEqual([firstPage[2]]);
    });

    it("searches as the user types, without pinning the selection atop the results", async () => {
        const source = createSource();

        const { element } = await mount({
            source,
            value: offPageItem.pk,
            selectedObject: offPageItem,
        });

        await type(element, "br");

        expect(source.fetchObjects, "Query is passed to the source").toHaveBeenLastCalledWith("br");
        expect(optionLabels(element), "Only matches are listed").toEqual(["Bravo"]);
    });

    it("chooses an option with the keyboard", async () => {
        const { element, form } = await mount();

        key(element, "ArrowDown");
        await element.updateComplete;

        expect(element.open, "ArrowDown opens the listbox").toBe(true);

        key(element, "ArrowDown");
        key(element, "ArrowDown");
        await element.updateComplete;

        expect(
            input(element).getAttribute("aria-activedescendant"),
            "Second option is active",
        ).toBe("option-2");

        key(element, "Enter");
        await element.updateComplete;

        expect(element.value, "Enter chooses the active option").toBe("2");
        expect(new FormData(form).get("item"), "Form sees the value").toBe("2");
        expect(element.open, "Choosing closes the listbox").toBe(false);
    });

    it("chooses an option by clicking its description", async () => {
        const { element } = await mount();

        element.show();
        await element.updateComplete;

        element.renderRoot
            .querySelector<HTMLElement>("#option-3 .ak-c-search-select__option-description")!
            .click();

        expect(element.value, "Clicking the description chooses the option").toBe("3");
    });

    it("is invalid while required and empty", async () => {
        const { element, form } = await mount({ required: true });

        expect(form.checkValidity(), "Empty required select blocks the form").toBe(false);

        element.select(firstPage[0]);

        expect(form.checkValidity(), "A selection makes it valid").toBe(true);
    });

    it("settles only once the latest fetch has landed", async () => {
        let release!: () => void;

        const source = createSource({
            fetchObjects: () =>
                new Promise<Item[]>((resolve) => {
                    release = () => resolve(firstPage);
                }),
            preselect: (objects) => objects[0],
        });

        const form = document.body.appendChild(document.createElement("form"));
        mounted.add(form);

        const element = new SearchSelect<Item>();
        element.source = source;
        form.appendChild(element);

        let settled = false;

        const waiting = element.settled.then(() => {
            settled = true;
        });

        await element.updateComplete;
        expect(settled, "Not settled while the fetch is pending").toBe(false);

        release();
        await waiting;

        expect(element.value, "Preselected default is in place once settled").toBe("1");
    });

    it("clears the selection with the blank option", async () => {
        const { element } = await mount({ value: "1", blankable: true });

        element.show();
        await element.updateComplete;

        element.renderRoot.querySelector<HTMLElement>("#option-blank")!.click();

        expect(element.value, "Blank option clears the value").toBe("");
        expect(element.toJSON(), "An empty select serializes as null").toBeNull();
    });

    it("announces the pinned action instead of choosing it", async () => {
        const { element } = await mount({ value: "1", actionLabel: "Create new..." });
        const onAction = vi.fn();

        element.addEventListener(SearchSelectActionEvent.eventName, onAction);

        element.show();
        await element.updateComplete;

        element.renderRoot.querySelector<HTMLElement>("#option-action")!.click();

        expect(onAction, "Action is announced").toHaveBeenCalledOnce();
        expect(element.value, "Selection is unchanged").toBe("1");
    });

    it("closes when clicking outside, even when focus stays in the input", async () => {
        const { element, form } = await mount();
        const outside = form.insertBefore(document.createElement("p"), element);
        outside.textContent = "Outside";
        outside.addEventListener("mousedown", (event) => event.preventDefault());

        await userEvent.click(input(element));
        await element.updateComplete;

        expect(element.open, "Clicking the input opens the listbox").toBe(true);

        await userEvent.click(outside);
        await element.updateComplete;

        expect(element.renderRoot.activeElement, "Focus stayed in the input").toBe(input(element));
        expect(element.open, "Clicking outside closes it").toBe(false);
    });

    it("toggles when clicking the input", async () => {
        const { element } = await mount();

        await userEvent.click(input(element));
        await userEvent.click(input(element));
        await element.updateComplete;

        expect(element.open, "A second click closes it").toBe(false);

        await userEvent.click(input(element));
        await element.updateComplete;

        expect(element.open, "A third click opens it again").toBe(true);
    });

    it("chooses an option with a real click", async () => {
        const { element } = await mount();

        await userEvent.click(input(element));
        await element.updateComplete;

        await userEvent.click(element.renderRoot.querySelector<HTMLElement>("#option-2")!);
        await element.updateComplete;

        expect(element.value, "Clicked option is chosen").toBe("2");
        expect(element.open, "Choosing closes the listbox").toBe(false);
    });

    it("stays open when a preselected default lands after the user opened it", async () => {
        let release!: () => void;

        const source = createSource({
            fetchObjects: () =>
                new Promise<Item[]>((resolve) => {
                    release = () => resolve(firstPage);
                }),
            preselect: (objects) => objects[0],
        });

        const form = document.body.appendChild(document.createElement("form"));
        mounted.add(form);

        const element = new SearchSelect<Item>();
        element.source = source;
        form.appendChild(element);
        await element.updateComplete;

        element.show();
        release();
        await element.settled;

        expect(element.value, "The default is applied").toBe("1");
        expect(element.open, "The listbox stays open").toBe(true);
    });
});
