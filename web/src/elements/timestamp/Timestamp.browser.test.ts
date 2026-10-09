import "./ak-timestamp";
import { AKTimestamp } from "./ak-timestamp";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const NOW = new Date("2026-06-15T12:00:00.000Z");
const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

const mounted = new Set<HTMLElement>();

interface MountInit {
    timestamp?: Date | string | number | null;
    hideElapsed?: boolean;
    datetime?: boolean;
    dateOnly?: boolean;
    refresh?: boolean;
    visible?: boolean;
    label?: string;
}

async function mount(init: MountInit = {}): Promise<AKTimestamp> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);

    const element = new AKTimestamp();

    element.timestamp =
        init.timestamp === undefined ? new Date(NOW.getTime() - HOUR) : init.timestamp;

    element.hideElapsed = init.hideElapsed ?? false;
    element.datetime = init.datetime ?? false;
    element.dateOnly = init.dateOnly ?? false;
    element.refresh = init.refresh ?? false;

    if (init.label) {
        element.textContent = init.label;
    }

    container.appendChild(element);
    await element.updateComplete;

    // The IntersectionObserver decorator owns `visible` in production. Tests set it directly so
    // that they do not depend on layout or scroll position.
    if (init.visible !== undefined) {
        // Let the real observer deliver its initial report first, or it overwrites the override.
        await vi.waitFor(() => expect(element.visible).toBe(true));

        element.visible = init.visible;
        await element.updateComplete;
    }

    return element;
}

const part = (element: AKTimestamp, name: string) =>
    element.renderRoot.querySelector<HTMLElement>(`[part="${name}"]`);

const text = (element: AKTimestamp, name: string) =>
    part(element, name)?.textContent?.replace(/\s+/g, " ").trim();

/**
 * Let the `requestAnimationFrame` that `updated()` schedules run, so that `startInterval()` has
 * been called, then re-render.
 */
async function settle(element: AKTimestamp): Promise<void> {
    // Fake rAF fires on a 16ms cadence.
    await vi.advanceTimersByTimeAsync(16);
    await element.updateComplete;
}

async function tick(element: AKTimestamp, ms: number): Promise<void> {
    await vi.advanceTimersByTimeAsync(ms);
    await element.updateComplete;
}

interface ReducedMotionStub {
    mediaQueryList: MediaQueryList;
    set(matches: boolean): void;
}

function stubReducedMotion(matches: boolean): ReducedMotionStub {
    // The media query list is cached on the class; every test must start without one.
    AKTimestamp["reducedMotionMediaQuery"] = null;

    const mediaQueryList = Object.assign(new EventTarget(), {
        matches,
        media: "(prefers-reduced-motion: reduce)",
    }) as unknown as MediaQueryList;

    vi.spyOn(window, "matchMedia").mockReturnValue(mediaQueryList);

    return {
        mediaQueryList,
        set(next) {
            Object.assign(mediaQueryList, { matches: next });
            mediaQueryList.dispatchEvent(new Event("change"));
        },
    };
}

function stubVisibility(state: DocumentVisibilityState) {
    const spy = vi.spyOn(document, "visibilityState", "get").mockReturnValue(state);

    return {
        set(next: DocumentVisibilityState) {
            spy.mockReturnValue(next);
            document.dispatchEvent(new Event("visibilitychange"));
        },
    };
}

beforeEach(() => {
    // `setTimeout` stays real: Lit and `vi.waitFor` need it.
    vi.useFakeTimers({
        now: NOW,
        toFake: [
            "Date",
            "setInterval",
            "clearInterval",
            "requestAnimationFrame",
            "cancelAnimationFrame",
        ],
    });

    AKTimestamp["reducedMotionMediaQuery"] = null;
});

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
    vi.useRealTimers();
    vi.restoreAllMocks();
});

describe("ak-timestamp: rendering", () => {
    it("renders a <time> element carrying the ISO timestamp", async () => {
        const element = await mount({ timestamp: new Date("2026-06-15T10:00:00.000Z") });
        const time = element.renderRoot.querySelector("time")!;

        expect(time.getAttribute("datetime")).toBe("2026-06-15T10:00:00.000Z");
    });

    it("renders the elapsed time by default", async () => {
        const element = await mount({ timestamp: new Date(NOW.getTime() - 2 * HOUR) });

        expect(text(element, "elapsed")).toBe("2 hours ago");
    });

    it("renders future timestamps", async () => {
        const element = await mount({ timestamp: new Date(NOW.getTime() + 3 * HOUR) });

        expect(text(element, "elapsed")).toBe("in 3 hours");
    });

    it("omits the elapsed time when hideElapsed is set", async () => {
        const element = await mount({ hideElapsed: true });

        expect(part(element, "elapsed")).toBeNull();
    });

    it("omits the datetime by default", async () => {
        const element = await mount();

        expect(part(element, "datetime")).toBeNull();
    });

    it("renders the full local date and time when datetime is set", async () => {
        const timestamp = new Date("2026-06-15T10:30:00.000Z");
        const element = await mount({ timestamp, datetime: true });

        expect(text(element, "datetime")).toBe(timestamp.toLocaleString());
    });

    it("renders only the local date when dateOnly is set", async () => {
        const timestamp = new Date("2026-06-15T10:30:00.000Z");
        const element = await mount({ timestamp, datetime: true, dateOnly: true });

        expect(text(element, "datetime")).toBe(timestamp.toLocaleDateString());
    });

    it("ignores dateOnly when datetime is not set", async () => {
        const element = await mount({ dateOnly: true });

        expect(part(element, "datetime")).toBeNull();
    });

    it("projects slotted content into the label part", async () => {
        const element = await mount({ label: "Last login" });
        const slot = part(element, "label")!.querySelector("slot")!;

        expect(slot.assignedNodes().map((node) => node.textContent)).toStrictEqual(["Last login"]);
    });

    it("updates when the timestamp changes", async () => {
        const element = await mount({ timestamp: new Date(NOW.getTime() - HOUR) });

        element.timestamp = new Date(NOW.getTime() - 5 * HOUR);
        await element.updateComplete;

        expect(text(element, "elapsed")).toBe("5 hours ago");
    });
});

describe("ak-timestamp: timestamp coercion", () => {
    it("accepts a Date", async () => {
        const element = await mount({ timestamp: new Date(NOW.getTime() - HOUR) });

        expect(element.timestamp).toBeInstanceOf(Date);
    });

    it("accepts an ISO string", async () => {
        const element = await mount({ timestamp: "2026-06-15T10:00:00.000Z" });

        expect(element.timestamp?.getTime()).toBe(Date.parse("2026-06-15T10:00:00.000Z"));
        expect(text(element, "elapsed")).toBe("2 hours ago");
    });

    it("accepts epoch milliseconds", async () => {
        const element = await mount({ timestamp: NOW.getTime() - HOUR - MINUTE });

        expect(text(element, "elapsed")).toBe("1 hour ago");
    });

    it("does not re-render when given an equal Date", async () => {
        const element = await mount({ timestamp: new Date(NOW.getTime() - HOUR) });
        const update = vi.spyOn(element, "requestUpdate");

        element.timestamp = new Date(NOW.getTime() - HOUR);
        await element.updateComplete;

        expect(update).not.toHaveBeenCalledWith("timestamp", expect.anything());
    });
});

describe("ak-timestamp: empty states", () => {
    it.each([
        ["null", null],
        ["zero", 0],
        ["the epoch", new Date(0)],
    ])("renders a placeholder for %s", async (_label, timestamp) => {
        const element = await mount({ timestamp });
        const placeholder = element.renderRoot.querySelector("span")!;

        expect(element.renderRoot.querySelector("time")).toBeNull();
        expect(placeholder.textContent).toBe("-");
        expect(placeholder.getAttribute("role")).toBe("time");
        expect(placeholder.getAttribute("aria-label")).toBe("None");
    });

    it("recovers from the placeholder when given a timestamp", async () => {
        const element = await mount({ timestamp: null });

        element.timestamp = new Date(NOW.getTime() - HOUR);
        await element.updateComplete;

        expect(element.renderRoot.querySelector("time")).not.toBeNull();
    });

    it.each([
        ["an unparseable string", "not a date"],
        ["an Invalid Date", new Date("not a date")],
        ["NaN", Number.NaN],
    ])("renders a placeholder for %s", async (_label, timestamp) => {
        const element = await mount({ timestamp });

        expect(element.timestamp).toBeNull();
        expect(element.renderRoot.querySelector("time")).toBeNull();
        expect(element.renderRoot.querySelector("span")!.textContent).toBe("-");
    });
});

describe("ak-timestamp: accessibility", () => {
    it("labels the time element by its slotted label", async () => {
        const element = await mount();
        const time = element.renderRoot.querySelector("time")!;
        const label = part(element, "label")!;

        expect(time.getAttribute("aria-labelledby")).toBe(label.id);
    });

    it("describes the time element by the elapsed part", async () => {
        const element = await mount();
        const time = element.renderRoot.querySelector("time")!;
        const elapsed = part(element, "elapsed")!;

        expect(time.getAttribute("aria-describedby")).toBe(elapsed.id);
    });

    it("drops aria-describedby when the elapsed part is not rendered", async () => {
        const element = await mount({ hideElapsed: true });
        const time = element.renderRoot.querySelector("time")!;

        expect(time.hasAttribute("aria-describedby")).toBe(false);
    });
});

describe("ak-timestamp: refresh", () => {
    it("does not refresh unless refresh is set", async () => {
        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            visible: true,
        });

        await settle(element);

        await tick(element, 10 * SECOND);

        expect(text(element, "elapsed")).toBe("30 seconds ago");
    });

    it("does not refresh while the element is not visible", async () => {
        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: false,
        });

        await settle(element);

        await tick(element, 10 * SECOND);

        expect(text(element, "elapsed")).toBe("30 seconds ago");
    });

    it("refreshes every second while within a minute of the timestamp", async () => {
        stubReducedMotion(false);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        await tick(element, 5 * SECOND);

        expect(text(element, "elapsed")).toBe("35 seconds ago");
    });

    it("refreshes every minute once the timestamp is more than a minute away", async () => {
        stubReducedMotion(false);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 5 * MINUTE),
            refresh: true,
            visible: true,
        });

        await settle(element);

        await tick(element, 30 * SECOND);
        expect(text(element, "elapsed")).toBe("5 minutes ago");

        await tick(element, 30 * SECOND);
        expect(text(element, "elapsed")).toBe("6 minutes ago");
    });

    it("drops to the slow cadence after crossing the one minute boundary", async () => {
        stubReducedMotion(false);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 55 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        const update = vi.spyOn(element, "requestUpdate");

        // Cross the boundary, then watch a full 30 seconds: only the minute cadence may remain.
        await tick(element, 10 * SECOND);
        update.mockClear();
        await tick(element, 30 * SECOND);

        expect(update).not.toHaveBeenCalled();
    });

    it("refreshes only once a minute when the user prefers reduced motion", async () => {
        stubReducedMotion(true);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        await tick(element, 10 * SECOND);
        expect(text(element, "elapsed")).toBe("30 seconds ago");

        // 90 seconds elapsed, which rounds to 2 minutes.
        await tick(element, 50 * SECOND);
        expect(text(element, "elapsed")).toBe("2 minutes ago");
    });

    it("stops refreshing when it becomes invisible", async () => {
        stubReducedMotion(false);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        element.visible = false;
        await settle(element);

        await tick(element, 10 * SECOND);

        expect(text(element, "elapsed")).toBe("30 seconds ago");
    });

    it("stops refreshing when disconnected", async () => {
        stubReducedMotion(false);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        const update = vi.spyOn(element, "requestUpdate");

        element.remove();
        await tick(element, 10 * SECOND);

        expect(update).not.toHaveBeenCalled();
    });

    it("does not leak intervals when the timestamp changes repeatedly", async () => {
        stubReducedMotion(false);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        for (let i = 1; i <= 5; i++) {
            element.timestamp = new Date(NOW.getTime() - (30 + i) * SECOND);
            await settle(element);
        }

        expect(vi.getTimerCount()).toBe(1);
    });
});

describe("ak-timestamp: reduced motion preference changes", () => {
    it("slows down when the preference is enabled mid-session", async () => {
        const motion = stubReducedMotion(false);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        await tick(element, 5 * SECOND);
        expect(text(element, "elapsed")).toBe("35 seconds ago");

        motion.set(true);

        await tick(element, 10 * SECOND);
        expect(text(element, "elapsed")).toBe("35 seconds ago");

        await tick(element, 50 * SECOND);
        expect(text(element, "elapsed")).toBe("2 minutes ago");
    });

    it("speeds up when the preference is disabled mid-session", async () => {
        const motion = stubReducedMotion(true);

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        motion.set(false);

        await tick(element, 5 * SECOND);
        expect(text(element, "elapsed")).toBe("35 seconds ago");
    });

    it("stops listening when disconnected", async () => {
        const motion = stubReducedMotion(false);
        const remove = vi.spyOn(motion.mediaQueryList, "removeEventListener");
        const element = await mount({ refresh: true, visible: true });
        await settle(element);

        element.remove();

        expect(remove).toHaveBeenCalledWith("change", element.startInterval);
    });
});

describe("ak-timestamp: document visibility", () => {
    it("starts refreshing when a hidden document becomes visible", async () => {
        stubReducedMotion(false);
        const visibility = stubVisibility("hidden");

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);

        await tick(element, 5 * SECOND);
        expect(text(element, "elapsed")).toBe("30 seconds ago");

        visibility.set("visible");
        await tick(element, 5 * SECOND);

        expect(text(element, "elapsed")).toBe("40 seconds ago");
    });

    it("clears the timer when the document is hidden", async () => {
        stubReducedMotion(false);
        const visibility = stubVisibility("visible");

        const element = await mount({
            timestamp: new Date(NOW.getTime() - 30 * SECOND),
            refresh: true,
            visible: true,
        });

        await settle(element);
        expect(vi.getTimerCount()).toBe(1);

        visibility.set("hidden");

        expect(vi.getTimerCount()).toBe(0);
    });

    it("stops listening when disconnected", async () => {
        stubReducedMotion(false);
        const visibility = stubVisibility("hidden");

        const element = await mount({ refresh: true, visible: true });
        await settle(element);

        element.remove();
        visibility.set("visible");

        expect(vi.getTimerCount()).toBe(0);
    });
});
