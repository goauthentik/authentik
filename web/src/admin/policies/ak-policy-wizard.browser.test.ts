import { PolicyWizard } from "#admin/policies/ak-policy-wizard";

import { CoreApi, PoliciesApi, type TypeCreate } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { page, userEvent } from "vitest/browser";

const dummyType: TypeCreate = {
    name: "Dummy Policy",
    description: "Used for testing.",
    component: "ak-policy-dummy-form",
    modelName: "dummypolicy",
};

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

    vi.spyOn(PoliciesApi.prototype, "policiesAllTypesList").mockResolvedValue([dummyType]);
    vi.spyOn(PoliciesApi.prototype, "policiesBindingsList").mockResolvedValue(empty);
    vi.spyOn(PoliciesApi.prototype, "policiesAllList").mockResolvedValue(empty);
    vi.spyOn(CoreApi.prototype, "coreGroupsList").mockResolvedValue(empty);
    vi.spyOn(CoreApi.prototype, "coreUsersList").mockResolvedValue(empty);
});

afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
});

const bindUserOption = page.getByRole("radio", { name: "Bind a user" });
const typeOption = page.getByRole("radio", { name: "Dummy Policy" });

async function back(element: PolicyWizard) {
    await userEvent.click(
        element.wizard!.renderRoot.querySelector<HTMLButtonElement>(
            '[data-test-id="wizard-navigation-previous"]',
        )!,
    );

    await expect.poll(() => element.wizard?.activeStep).toBe("initial");
}

describe("ak-policy-wizard", () => {
    it("forgets the bind choice when a policy type is chosen after going back", async () => {
        const element = new PolicyWizard();
        element.showBindingPage = true;
        element.bindingTarget = "target";
        document.body.append(element);

        await expect.element(bindUserOption).toBeVisible();
        await expect.element(typeOption).toBeVisible();

        await userEvent.click(bindUserOption);
        await expect.poll(() => element.wizard?.activeStep).toBe("create-binding");

        await back(element);

        await userEvent.click(typeOption);

        await expect
            .poll(() => element.wizard?.activeStep)
            .toBe("type-ak-policy-dummy-form-dummypolicy");

        // The binding page would otherwise offer a user instead of the new policy.
        expect(element.wizard?.state).not.toHaveProperty("initial");

        await back(element);
        await expect.element(bindUserOption).not.toBeChecked();
        await expect.element(typeOption).toBeChecked();
    });
});
