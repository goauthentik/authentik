import "#admin/stages/deny/DenyStageForm";
import { AKRefreshEvent } from "#common/events";

import { StageDuplicateButton } from "#admin/stages/StageDuplicateForm";

import { DenyStage, Stage, StagesApi } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { page } from "vitest/browser";

import { LitElement, render } from "lit";

// Dialogs open inside the interface's render root, as in the Admin interface.
class TestInterface extends LitElement {}
customElements.define("test-stage-duplicate-interface", TestInterface);

let root: TestInterface;

beforeEach(() => {
    root = new TestInterface();
    root.id = "interface-root";
    document.body.append(root);
});

afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
});

function mountButton(original: Stage) {
    const container = document.createElement("div");
    root.renderRoot.append(container);
    render(StageDuplicateButton(original), container);

    const refreshes = vi.fn();
    container.addEventListener(AKRefreshEvent.eventName, refreshes);

    return refreshes;
}

function stage(pk: string, name: string): Stage {
    return {
        pk,
        name,
        component: "ak-stage-deny-form",
        verboseName: "Deny Stage",
        verboseNamePlural: "Deny Stages",
        metaModelName: "authentik_stages_deny.denystage",
        flowSet: [],
    };
}

describe("StageDuplicateButton", () => {
    it("creates a copy under the given name and opens it for editing", async () => {
        const original = stage("original", "deny");
        const copy = stage("copy", "deny-for-admins");

        const duplicate = vi
            .spyOn(StagesApi.prototype, "stagesAllDuplicateCreate")
            .mockResolvedValue(copy);

        vi.spyOn(StagesApi.prototype, "stagesDenyRetrieve").mockResolvedValue({
            ...copy,
            denyMessage: "",
        } as DenyStage);

        const refreshes = mountButton(original);

        await page.getByRole("button", { name: 'Duplicate "deny"', exact: true }).click();

        const name = page.getByRole("dialog").getByRole("textbox", { name: "Stage Name" });
        await expect.element(name).toHaveValue("deny (copy)");
        await name.fill("deny-for-admins");
        await page.getByRole("dialog").getByRole("button", { name: "Duplicate" }).click();

        await expect
            .poll(() => duplicate.mock.calls)
            .toEqual([
                [{ stageUuid: "original", stageDuplicateRequest: { name: "deny-for-admins" } }],
            ]);

        await expect
            .poll(() => root.renderRoot.querySelector("ak-stage-deny-form")?.instancePk)
            .toBe("copy");

        expect(root.renderRoot.querySelector("ak-stage-duplicate-form")).toBeNull();
        // The table holding the button refreshes, so it lists the copy.
        expect(refreshes).toHaveBeenCalled();
    });

    it("opens nothing else when the duplicate modal is closed", async () => {
        const duplicate = vi.spyOn(StagesApi.prototype, "stagesAllDuplicateCreate");

        mountButton(stage("original", "deny"));

        await page.getByRole("button", { name: 'Duplicate "deny"', exact: true }).click();
        await expect.element(page.getByRole("dialog")).toBeVisible();
        await page.getByRole("dialog").getByRole("button", { name: "Close" }).first().click();

        await expect.poll(() => root.renderRoot.querySelector("dialog")).toBeNull();
        expect(duplicate).not.toHaveBeenCalled();
        expect(root.renderRoot.querySelector("ak-stage-deny-form")).toBeNull();
    });
});
