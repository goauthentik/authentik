import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PageFixture, PageFixtureInit } from "#e2e/fixtures/PageFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { series } from "#packages/core/promises";

import { expect, Locator } from "@playwright/test";

export interface BindIdentificationStageInit {
    /**
     * The slug of the flow to bind the stage to.
     */
    flowSlug: string;

    /**
     * The name to give the created stage.
     */
    name: string;

    /**
     * Names of sources the stage must offer, as they appear in the source picker.
     */
    sources?: string[];

    /**
     * The binding order within the flow. Stages run lowest-first.
     */
    order?: number;
}

export interface FlowFixtureInit extends PageFixtureInit {
    form: FormFixture;
    pointer: PointerFixture;
    navigator: NavigatorFixture;
}

/**
 * Builds flows and binds stages to them through the admin UI.
 */
export class FlowFixture extends PageFixture {
    public static readonly fixtureName = "Flow";

    protected readonly form: FormFixture;
    protected readonly pointer: PointerFixture;
    protected readonly navigator: NavigatorFixture;

    constructor({ page, testName, form, pointer, navigator }: FlowFixtureInit) {
        super({ page, testName });

        this.form = form;
        this.pointer = pointer;
        this.navigator = navigator;
    }

    /**
     * Create an empty authentication flow and return its slug.
     */
    public createFlow = async (name: string, slug: string): Promise<string> => {
        const { page, form, pointer, logger } = this;
        const { fill } = form;

        await this.navigator.navigate("/if/admin/flow/flows");

        const dialog = page.getByRole("dialog", { name: "New Flow" });

        await pointer.click("New Flow");
        await expect(dialog, "Flow form opens").toBeVisible();

        await series(
            [fill, "Flow Name", name, dialog],
            [fill, "Title", name, dialog],
            [fill, "Slug", slug, dialog],
        );

        await dialog.getByLabel("Designation").selectOption("authentication");

        await pointer.click("Create Flow", "button", dialog);

        // Every save here is a round-trip to one shared authentik instance that the other
        // workers are also writing to, so this is slower than a typical dialog dismissal.
        await expect(dialog, "Flow form closes after save").toBeHidden({ timeout: 30_000 });

        logger.info(`Created flow ${slug}`);

        return slug;
    };

    /**
     * Open the bind wizard on a flow's "Stage Bindings" tab and pick a stage type.
     *
     * @returns The wizard dialog, showing the new stage's form.
     */
    public openBindWizard = async (flowSlug: string, stageType: string): Promise<Locator> => {
        const { page, pointer, navigator } = this;

        await navigator.navigate(`/if/admin/flow/flows/${flowSlug}`);

        // The wizard relabels itself as it advances through its steps.
        const wizard = page.getByRole("dialog", {
            name: /New Stage Wizard|Create New Stage/,
        });

        // The bind wizard lives on the flow's "Stage Bindings" tab, not its overview.
        await page
            .getByRole("tab", { name: "Stage Bindings" })
            .or(page.getByRole("link", { name: "Stage Bindings" }))
            .click();

        await pointer.click("Create or bind...", "button", page.getByRole("toolbar"));
        await expect(wizard, "Bind wizard opens").toBeVisible({ timeout: 10_000 });

        await wizard.getByRole("radio", { name: stageType }).check();
        await page.getByTestId("wizard-navigation-next").click();

        return wizard;
    };

    /**
     * Save the stage form in the bind wizard, then bind the stage at `order`.
     */
    public finishBindWizard = async (
        wizard: Locator,
        name: string,
        order: number,
    ): Promise<void> => {
        const { page, form } = this;

        await page.getByTestId("wizard-navigation-next").click();

        const stageInput = wizard.getByRole("textbox", { name: "Stage" });

        await expect(stageInput, "Wizard back-fills the created stage").toHaveValue(name, {
            timeout: 20_000,
        });

        // Filled after the stage, because adopting the stage re-renders this step and would
        // discard an order typed beforehand.
        await form.fill("Order", order.toString(), wizard);

        await page.getByTestId("wizard-navigation-next").click();

        await expect(wizard, "Bind wizard closes after save").toBeHidden({ timeout: 30_000 });
    };

    /**
     * Create an identification stage offering the given sources, and bind it to a flow.
     */
    public bindIdentificationStage = async ({
        flowSlug,
        name,
        sources = [],
        order = 10,
    }: BindIdentificationStageInit): Promise<void> => {
        const wizard = await this.openBindWizard(flowSlug, "Identification Stage");

        await this.form.fill("Stage Name", name, wizard);

        if (sources.length) {
            await this.form.setFormGroup(/Source settings/, true, wizard);
        }

        for (const source of sources) {
            await this.selectSource(wizard, source);
        }

        await this.finishBindWizard(wizard, name, order);

        this.logger.info(`Bound identification stage ${name} to ${flowSlug}`);
    };

    /**
     * Move a source into the stage's selected sources, unless it is already there.
     *
     * A new stage preselects sources on its own, so the selected pane is checked first.
     */
    protected selectSource = async (wizard: Locator, source: string): Promise<void> => {
        // The stage form's only dual list.
        const picker = wizard.locator("ak-dual-select-dynamic-selected");

        const selected = picker
            .locator("ak-dual-select-selected-pane")
            .getByRole("option", { name: source });

        if (await selected.count()) return;

        await picker.getByRole("searchbox", { name: "Search Available Sources..." }).fill(source);

        await picker
            .locator("ak-dual-select-available-pane")
            .getByRole("option", { name: source })
            .dblclick();

        await expect(selected, `Source "${source}" is selected`).toBeVisible();
    };
}
