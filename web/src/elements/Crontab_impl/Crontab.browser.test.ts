import "../Crontab";
import { akCrontab, Crontab } from "../Crontab";

import { afterEach, describe, expect, it } from "vitest";

import { render } from "lit";

const mounted = new Set<HTMLElement>();

interface MountInit {
    cron?: string | null;
    hideCrontab?: boolean;
}

async function mount(init: MountInit = {}): Promise<Crontab> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);

    const element = new Crontab();

    // `cronString` is private, so the `cron` attribute is the only public way in.
    if (init.cron !== undefined && init.cron !== null) {
        element.setAttribute("cron", init.cron);
    }

    element.hideCrontab = init.hideCrontab ?? false;

    container.appendChild(element);
    await element.updateComplete;

    return element;
}

const part = (element: Crontab, name: "cronstring" | "natural") =>
    element.renderRoot.querySelector<HTMLElement>(`[part="${name}"]`);

const text = (element: Crontab, name: "cronstring" | "natural") =>
    part(element, name)?.textContent?.replace(/\s+/g, " ").trim();

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-crontab: rendering", () => {
    it("shows the cron string and its description", async () => {
        const element = await mount({ cron: "*/5 * * * *" });

        expect(text(element, "cronstring")).toBe("*/5 * * * *");
        expect(text(element, "natural")).toBe("Every 5 minutes");
    });

    it("defaults to every minute", async () => {
        const element = await mount();

        expect(text(element, "cronstring")).toBe("* * * * *");
        expect(text(element, "natural")).toBe("Every minute");
    });

    it("describes a weekday schedule", async () => {
        const element = await mount({ cron: "0 9 * * 1-5" });

        expect(text(element, "natural")).toBe("At 09:00, Monday through Friday");
    });

    it("renders times in 24 hour format", async () => {
        const element = await mount({ cron: "30 14 * * *" });

        expect(text(element, "natural")).toBe("At 14:30");
    });

    it("updates when the cron attribute changes", async () => {
        const element = await mount({ cron: "*/5 * * * *" });

        element.setAttribute("cron", "30 14 * * *");
        await element.updateComplete;

        expect(text(element, "cronstring")).toBe("30 14 * * *");
        expect(text(element, "natural")).toBe("At 14:30");
    });
});

describe("ak-crontab: hide-crontab", () => {
    it("omits the cron string and keeps the description", async () => {
        const element = await mount({ cron: "*/5 * * * *", hideCrontab: true });

        expect(part(element, "cronstring")).toBeNull();
        expect(text(element, "natural")).toBe("Every 5 minutes");
    });

    it("reflects the hide-crontab attribute", async () => {
        const element = await mount({ cron: "*/5 * * * *" });

        element.setAttribute("hide-crontab", "");
        await element.updateComplete;

        expect(element.hideCrontab).toBe(true);
        expect(part(element, "cronstring")).toBeNull();
    });
});

describe("ak-crontab: invalid input", () => {
    it.each([
        ["too few fields", "nope"],
        ["an empty string", ""],
        ["an out-of-range minute", "60 * * * *"],
        ["an out-of-range weekday", "0 0 * * 8"],
    ])("falls back to a message for %s", async (_label, cron) => {
        const element = await mount({ cron });

        expect(text(element, "natural")).toBe("Cron string does not parse.");
    });

    it("still shows the offending string so it can be corrected", async () => {
        const element = await mount({ cron: "nope" });

        expect(text(element, "cronstring")).toBe("nope");
    });

    it("does not throw when the cron attribute is removed", async () => {
        const element = await mount({ cron: "*/5 * * * *" });

        element.removeAttribute("cron");
        await element.updateComplete;

        expect(text(element, "natural")).toBe("Cron string does not parse.");
    });
});

describe("ak-crontab: akCrontab helper", () => {
    function renderHelper(options: Parameters<typeof akCrontab>[0]): Crontab {
        const container = document.body.appendChild(document.createElement("div"));
        mounted.add(container);

        render(akCrontab(options), container);

        return container.querySelector("ak-crontab")!;
    }

    it("renders an ak-crontab with the given cron", async () => {
        const element = renderHelper({ cron: "30 14 * * *" });
        await element.updateComplete;

        expect(text(element, "natural")).toBe("At 14:30");
    });

    it("forwards hideCrontab as the hide-crontab attribute", async () => {
        const element = renderHelper({ cron: "30 14 * * *", hideCrontab: true });
        await element.updateComplete;

        expect(element.hasAttribute("hide-crontab")).toBe(true);
        expect(part(element, "cronstring")).toBeNull();
    });

    it("leaves the default cron when none is given", async () => {
        const element = renderHelper({});
        await element.updateComplete;

        expect(element.hasAttribute("cron")).toBe(false);
        expect(text(element, "natural")).toBe("Every minute");
    });

    it("spreads remaining options onto the element", async () => {
        const element = renderHelper({ cron: "30 14 * * *", class: "schedule" });
        await element.updateComplete;

        expect(element.classList.contains("schedule")).toBe(true);
    });
});
