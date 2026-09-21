import "../Paginator";
import { Paginator, PageChangeEvent } from "../Paginator";

import { afterEach, describe, expect, it, vi } from "vitest";

const mounted = new Set<HTMLElement>();

interface MountInit {
    itemCount?: number;
    itemsPerPage?: number;
    page?: number;
    compact?: boolean;
    disabled?: boolean;
    label?: string;
}

async function mount(init: MountInit = {}): Promise<Paginator> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);

    const element = new Paginator();

    element.itemCount = init.itemCount ?? 427;
    element.itemsPerPage = init.itemsPerPage ?? 20;
    element.page = init.page ?? 1;
    element.compact = init.compact ?? false;
    element.disabled = init.disabled ?? false;
    element.label = init.label ?? null;

    container.appendChild(element);
    await element.updateComplete;

    return element;
}

/**
 * Collect every `ak-page-changed` the component dispatches, and send each one back onto `page` the
 * way a real host does.
 */
function trackAndEcho(element: Paginator): number[] {
    const seen: number[] = [];

    element.addEventListener(PageChangeEvent.eventName, (event) => {
        seen.push(event.page);
        element.page = event.page;
    });

    return seen;
}

function control(element: Paginator, action: "first" | "prev" | "next" | "last") {
    return element.renderRoot.querySelector<HTMLButtonElement>(`button[data-action="${action}"]`);
}

function summary(element: Paginator): string {
    return element.renderRoot
        .querySelector('[part="total-count"]')!
        .textContent!.replace(/\s+/g, " ")
        .trim();
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-pagination: navigation", () => {
    it("goes to the next page when > is pressed", async () => {
        const element = await mount({ page: 2 });
        const seen = trackAndEcho(element);

        control(element, "next")!.click();
        await element.updateComplete;

        expect(seen).toStrictEqual([3]);
        expect(summary(element)).toBe("41 - 60 of 427");
    });

    it("goes back when < is pressed", async () => {
        const element = await mount({ page: 3 });
        const seen = trackAndEcho(element);

        control(element, "prev")!.click();
        await element.updateComplete;

        expect(seen).toStrictEqual([2]);
    });

    it("goes to the first page when << is pressed", async () => {
        const element = await mount({ page: 9 });
        const seen = trackAndEcho(element);

        control(element, "first")!.click();
        await element.updateComplete;

        expect(seen).toStrictEqual([1]);
    });

    it("goes to the last page when >> is pressed", async () => {
        const element = await mount({ page: 2 });
        const seen = trackAndEcho(element);

        control(element, "last")!.click();
        await element.updateComplete;

        expect(seen).toStrictEqual([22]);
        expect(summary(element)).toBe("421 - 427 of 427");
    });

    it("dispatches an event on page change", async () => {
        const element = await mount({ page: 1 });
        const seen: number[] = [];

        document.body.addEventListener(PageChangeEvent.eventName, (event) => {
            seen.push(event.page);
        });

        control(element, "next")!.click();

        expect(seen).toStrictEqual([2]);
    });
});

describe("ak-pagination: disabled states", () => {
    it("backward navigation disabled on the first page", async () => {
        const element = await mount({ page: 1 });

        expect(control(element, "first")!.disabled).toBe(true);
        expect(control(element, "prev")!.disabled).toBe(true);
        expect(control(element, "next")!.disabled).toBe(false);
        expect(control(element, "last")!.disabled).toBe(false);
    });

    it("forward navigation disabled on the last page", async () => {
        const element = await mount({ page: 22 });

        expect(control(element, "next")!.disabled).toBe(true);
        expect(control(element, "last")!.disabled).toBe(true);
        expect(control(element, "prev")!.disabled).toBe(false);
        expect(control(element, "first")!.disabled).toBe(false);
    });

    it("disables all navigation when there is only one page", async () => {
        const element = await mount({ itemCount: 10 });

        expect(control(element, "next")!.disabled).toBe(true);
        expect(control(element, "last")!.disabled).toBe(true);
        expect(control(element, "prev")!.disabled).toBe(true);
        expect(control(element, "first")!.disabled).toBe(true);
    });

    it("honors element disabled", async () => {
        const element = await mount({ page: 3, disabled: true });
        const seen = trackAndEcho(element);

        for (const action of ["first", "prev", "next", "last"] as const) {
            expect(control(element, action)!.disabled).toBe(true);
            control(element, action)!.click();
        }

        await element.updateComplete;

        expect(seen).toStrictEqual([]);
        expect(element.hasAttribute("disabled")).toBe(true);
    });
});

describe("ak-pagination: sizes", () => {
    it("renders all controls in the default size", async () => {
        const element = await mount();

        expect(control(element, "first")).not.toBeNull();
        expect(control(element, "last")).not.toBeNull();
        expect(control(element, "prev")).not.toBeNull();
        expect(control(element, "next")).not.toBeNull();
        expect(element.renderRoot.querySelector('[part="page-select"]')).not.toBeNull();
    });

    it("renders only the > and < controls when compact", async () => {
        const element = await mount({ compact: true });

        expect(control(element, "first")).toBeNull();
        expect(control(element, "last")).toBeNull();
        expect(element.renderRoot.querySelector('[part="page-select"]')).toBeNull();
        expect(control(element, "prev")).not.toBeNull();
        expect(control(element, "next")).not.toBeNull();
    });
});

describe("ak-pagination: edge ranges", () => {
    it("behaves correctly when there are zero items", async () => {
        const element = await mount({ itemCount: 0 });
        const seen = trackAndEcho(element);

        expect(summary(element)).toBe("0 - 0 of 0");

        for (const action of ["first", "prev", "next", "last"] as const) {
            expect(control(element, action)!.disabled).toBe(true);
        }

        await element.updateComplete;
        expect(seen).toStrictEqual([]);
    });

    it("behaves correctly when there is only one page", async () => {
        const element = await mount({ itemCount: 7 });

        expect(summary(element)).toBe("1 - 7 of 7");

        for (const action of ["first", "prev", "next", "last"] as const) {
            expect(control(element, action)!.disabled).toBe(true);
        }
    });
});

describe("ak-pagination: accessibility", () => {
    it("uses the generic aria label when none specified", async () => {
        const element = await mount();

        expect(element.renderRoot.querySelector("nav")!.getAttribute("aria-label")).toBe(
            "Pagination"
        );
    });

    it("uses the label when specified", async () => {
        const element = await mount({ label: "Users" });

        expect(element.renderRoot.querySelector("nav")!.getAttribute("aria-label")).toBe(
            "Users pagination"
        );
    });

    it("gives every control an aria-label", async () => {
        const element = await mount();

        expect(control(element, "first")!.getAttribute("aria-label")).toBe("Go to first page");
        expect(control(element, "prev")!.getAttribute("aria-label")).toBe("Go to previous page");
        expect(control(element, "next")!.getAttribute("aria-label")).toBe("Go to next page");
        expect(control(element, "last")!.getAttribute("aria-label")).toBe("Go to last page");
    });
});

function pageInput(element: Paginator): HTMLInputElement {
    return element.renderRoot.querySelector<HTMLInputElement>('[part="page-select-control"]')!;
}

async function keyAndCommit(element: Paginator, value: string): Promise<void> {
    const input = pageInput(element);

    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
    await element.updateComplete;

    input.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Enter", bubbles: true, composed: true })
    );

    await element.updateComplete;
}

describe("ak-pagination: page select", () => {
    it("goes to a page via the input control", async () => {
        const element = await mount({ page: 1 });
        const seen = trackAndEcho(element);

        await keyAndCommit(element, "5");

        expect(seen).toStrictEqual([5]);
        expect(summary(element)).toBe("81 - 100 of 427");
    });

    it("narrows an out-of-range page on Enter", async () => {
        const element = await mount({ page: 1 });
        const seen = trackAndEcho(element);

        await keyAndCommit(element, "999");

        expect(seen).toStrictEqual([22]);
        expect(pageInput(element).value).toBe("22");
    });

    it("ignores a non-numeric entry on Enter", async () => {
        const element = await mount({ page: 4 });
        const seen = trackAndEcho(element);

        await keyAndCommit(element, "x");

        expect(seen).toStrictEqual([]);
        expect(pageInput(element).value).toBe("4");
    });

    it("reverts the pending on blur without Enter", async () => {
        const element = await mount({ page: 4 });
        const seen = trackAndEcho(element);
        const input = pageInput(element);

        input.value = "9";
        input.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        await element.updateComplete;

        input.dispatchEvent(new FocusEvent("blur", { bubbles: false, composed: true }));
        await element.updateComplete;

        expect(seen).toStrictEqual([]);
        expect(pageInput(element).value).toBe("4");
    });

    it("blocks non-digit keys but allows editing keys", async () => {
        const element = await mount();
        const input = pageInput(element);

        const letter = new KeyboardEvent("keydown", {
            key: "a",
            bubbles: true,
            composed: true,
            cancelable: true,
        });

        input.dispatchEvent(letter);
        expect(letter.defaultPrevented).toBe(true);

        const backspace = new KeyboardEvent("keydown", {
            key: "Backspace",
            bubbles: true,
            composed: true,
            cancelable: true,
        });

        input.dispatchEvent(backspace);
        expect(backspace.defaultPrevented).toBe(false);
    });

    it("disables the input when there is only one page", async () => {
        const element = await mount({ itemCount: 7 });
        expect(pageInput(element).disabled).toBe(true);
    });

    it("disables the input when the element is disabled", async () => {
        const element = await mount({ disabled: true });

        expect(pageInput(element).disabled).toBe(true);
    });

    it("sizes the input from the page-number width", async () => {
        const customProperty = "--ak-c-pagination__page-select--form-control--width";
        const element = await mount({ itemCount: 427, itemsPerPage: 20 });
        const nav = element.renderRoot.querySelector<HTMLElement>('[part="pagination"]')!;

        expect(nav.style.getPropertyValue(customProperty)).toBe("2ch");

        element.itemCount = 20_000;
        await element.updateComplete;

        expect(nav.style.getPropertyValue(customProperty)).toBe("4ch");
    });

    it("re-syncs the draft when the host changes the page", async () => {
        const element = await mount({ page: 1 });

        element.page = 6;
        await element.updateComplete;

        expect(pageInput(element).value).toBe("6");
    });
});

describe("ak-pagination: changing ranges", () => {
    it("does not leave the page if the range contains it after setting", async () => {
        const element = await mount({ itemCount: 427, page: 3 });
        const seen = trackAndEcho(element);

        element.itemCount = 200;
        await element.updateComplete;

        expect(seen).toStrictEqual([]);
        expect(element.page).toBe(3);
        expect(summary(element)).toBe("41 - 60 of 200");
    });

    it("goes to the last page and informs the client when the range no longer contains it", async () => {
        const element = await mount({ itemCount: 427, itemsPerPage: 20, page: 7 });
        const seen = trackAndEcho(element);

        element.itemCount = 50;
        await element.updateComplete;

        expect(seen).toStrictEqual([3]);
        expect(summary(element)).toBe("41 - 50 of 50");
    });

    it("does not send a second event when the client responds with the narrowed page number", async () => {
        const element = await mount({ itemCount: 427, page: 7 });
        const seen = trackAndEcho(element);

        element.itemCount = 50;
        await element.updateComplete;
        await element.updateComplete;

        await vi.waitFor(() => expect(seen).toStrictEqual([3]));
    });

    it("does not loop when the host ignores the event", async () => {
        const element = await mount({ itemCount: 427, page: 7 });
        const seen: number[] = [];

        element.addEventListener(PageChangeEvent.eventName, (event) => {
            seen.push(event.page);
        });

        element.itemCount = 50;
        await element.updateComplete;
        await element.updateComplete;

        expect(seen).toStrictEqual([3]);
    });

    it("narrows to page 1 when the range is empty", async () => {
        const element = await mount({ itemCount: 427, page: 7 });
        const seen = trackAndEcho(element);

        element.itemCount = 0;
        await element.updateComplete;

        expect(seen).toStrictEqual([1]);
        expect(summary(element)).toBe("0 - 0 of 0");
    });
});
