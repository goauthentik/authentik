import { AKStageWizard } from "#admin/stages/ak-stage-wizard";

import { FlowsApi, StagesApi, type TypeCreate } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { page, userEvent } from "vitest/browser";

const dummyType: TypeCreate = {
    name: "Dummy Stage",
    description: "Used for testing.",
    component: "ak-stage-dummy-form",
    modelName: "dummystage",
};

const typeStep = "type-ak-stage-dummy-form-dummystage";

beforeEach(() => {
    const empty = {
        results: [],
        autocomplete: {},
        pagination: {
            next: 0,
            previous: 0,
            count: 0,
            current: 1,
            totalPages: 1,
            startIndex: 0,
            endIndex: 0,
        },
    };

    vi.spyOn(StagesApi.prototype, "stagesAllTypesList").mockResolvedValue([dummyType]);
    vi.spyOn(StagesApi.prototype, "stagesAllList").mockResolvedValue(empty);
    vi.spyOn(FlowsApi.prototype, "flowsBindingsList").mockResolvedValue(empty);
});

afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
});

async function mount() {
    const element = new AKStageWizard();
    element.showBindingPage = true;
    element.bindingTarget = "flow";
    document.body.append(element);

    await expect.element(bindOption).toBeVisible();
    await expect.element(typeOption).toBeVisible();

    return element;
}

const bindOption = page.getByRole("radio", { name: "Bind existing stage" });
const typeOption = page.getByRole("radio", { name: "Dummy Stage" });

/**
 * Click an option's label text, as a person would.
 */
function choose(option: typeof bindOption) {
    return userEvent.click(option.element().closest("label")!.querySelector(".pf-c-radio__label")!);
}

function navigation(element: AKStageWizard, kind: "next" | "previous") {
    return element.wizard!.renderRoot.querySelector<HTMLButtonElement>(
        `[data-test-id="wizard-navigation-${kind}"]`,
    )!;
}

async function back(element: AKStageWizard) {
    await userEvent.click(navigation(element, "previous"));
    await expect.poll(() => element.wizard?.activeStep).toBe("initial");
}

describe("ak-stage-wizard", () => {
    it("binds an existing stage again after going back", async () => {
        const element = await mount();

        await choose(bindOption);
        await expect.poll(() => element.wizard?.activeStep).toBe("create-binding");

        await back(element);
        await expect.element(bindOption).toBeChecked();

        await choose(bindOption);
        await expect.poll(() => element.wizard?.activeStep).toBe("create-binding");

        await back(element);
        await expect.poll(() => navigation(element, "next").disabled).toBe(false);
        await userEvent.click(navigation(element, "next"));
        await expect.poll(() => element.wizard?.activeStep).toBe("create-binding");
    });

    it("binds an existing stage after a type was chosen", async () => {
        const element = await mount();

        await choose(typeOption);
        await expect.poll(() => element.wizard?.activeStep).toBe(typeStep);

        await back(element);
        await choose(bindOption);
        await expect.poll(() => element.wizard?.activeStep).toBe("create-binding");

        expect(element.wizard?.steps).toEqual(["initial", "create-binding"]);
        expect(element.selectedType).toBeNull();

        await back(element);
        await expect.element(bindOption).toBeChecked();
        await expect.element(typeOption).not.toBeChecked();
    });

    it("moves on when the chosen type is clicked again after going back", async () => {
        const element = await mount();

        await choose(typeOption);
        await expect.poll(() => element.wizard?.activeStep).toBe(typeStep);

        await back(element);
        await choose(typeOption);
        await expect.poll(() => element.wizard?.activeStep).toBe(typeStep);
    });
});
