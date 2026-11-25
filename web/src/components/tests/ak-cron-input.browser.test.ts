import "#components/ak-cron-input";
import { AKCronInput } from "#components/ak-cron-input";

import { afterEach, describe, expect, it } from "vitest";

const mounted = new Set<HTMLElement>();

async function mount(value?: string): Promise<AKCronInput> {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);

    const element = new AKCronInput();
    element.name = "crontab";
    element.label = "Crontab";

    if (value !== undefined) {
        element.value = value;
    }

    container.appendChild(element);
    await element.updateComplete;

    return element;
}

const input = (element: AKCronInput) => element.querySelector<HTMLInputElement>("input")!;

const help = (element: AKCronInput) => {
    const id = input(element).getAttribute("aria-describedby");

    return id ? document.getElementById(id) : null;
};

const helpText = (element: AKCronInput) => help(element)?.textContent?.replace(/\s+/g, " ").trim();

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-cron-input: description", () => {
    it("describes a valid entry", async () => {
        const element = await mount("*/5 * * * *");

        expect(helpText(element)).toBe("Every 5 minutes");
    });

    it("renders times in 24 hour format", async () => {
        const element = await mount("30 14 * * *");

        expect(helpText(element)).toBe("At 14:30");
    });

    it("shows a failure message when an entry will not parse", async () => {
        const element = await mount("not a cron");

        expect(helpText(element)).toBe("Cron string does not parse.");
    });

    it.each([
        ["a seconds field", "0 0 0 * * *"],
        ["a macro", "@daily"],
        ["Quartz L", "0 0 L * *"],
        ["Quartz W", "0 0 15W * *"],
        ["Quartz L in day-of-week", "0 0 * * 5L"],
        ["Quartz #", "0 0 * * 1#2"],
        ["Quartz ?", "0 0 ? * *"],
    ])("rejects %s, which the server does not accept", async (_label, value) => {
        const element = await mount(value);

        expect(helpText(element)).toBe("Cron string does not parse.");
    });

    it.each([
        ["ranges and steps", "1-10/2 9-17 * * 1-5"],
        ["lists", "0,30 * * * *"],
        ["month and weekday names", "0 0 * JAN-MAR MON-FRI"],
        ["lowercase names", "0 0 * * mon"],
    ])("describes %s, which the server accepts", async (_label, value) => {
        const element = await mount(value);

        expect(helpText(element)).not.toBe("Cron string does not parse.");
    });

    it.each([
        ["no value", undefined],
        ["an empty value", ""],
        ["only whitespace", "   "],
    ])("shows no help text for %s", async (_label, value) => {
        const element = await mount(value);

        expect(helpText(element)).toBe("");
    });

    it("hides the help text when the user clears the field", async () => {
        const element = await mount("*/5 * * * *");
        const control = input(element);

        control.value = "";
        control.dispatchEvent(new InputEvent("input", { bubbles: true }));
        await element.updateComplete;

        expect(helpText(element)).toBe("");
    });

    it("updates the description as the user types", async () => {
        const element = await mount("*/5 * * * *");
        const control = input(element);

        control.value = "0 9 * * 1-5";
        control.dispatchEvent(new InputEvent("input", { bubbles: true }));
        await element.updateComplete;

        expect(element.value).toBe("0 9 * * 1-5");
        expect(helpText(element)).toBe("At 09:00, Monday through Friday");
    });
});

describe("ak-cron-input: accessibility", () => {
    it("points aria-describedby at the rendered help element", async () => {
        const element = await mount("*/5 * * * *");
        const target = help(element);

        expect(target).not.toBeNull();
        expect(element.contains(target)).toBe(true);
    });

    it("labels the input", async () => {
        const element = await mount("*/5 * * * *");
        const control = input(element);
        const label = element.querySelector(`label[for="${control.id}"]`);

        expect(label?.textContent).toContain("Crontab");
    });
});
