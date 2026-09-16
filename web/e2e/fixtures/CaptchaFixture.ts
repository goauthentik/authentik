import type { CaptchaVendorConfig } from "#e2e/fixtures/captcha-vendors";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PageFixture, PageFixtureInit } from "#e2e/fixtures/PageFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { series } from "#packages/core/promises";

import { expect } from "@playwright/test";

export interface BindCaptchaStageInit {
    /**
     * The slug of the flow to bind the stage to.
     */
    flowSlug: string;

    vendor: CaptchaVendorConfig;

    /**
     * The name to give the created stage.
     */
    name: string;

    /**
     * The binding order within the flow. Stages run lowest-first.
     */
    order: number;

    /**
     * Whether the stage renders a visible widget. Defaults to `true`.
     */
    interactive?: boolean;

    /**
     * Use the vendor's self-solving site key so the flow advances unattended.
     */
    autoSolve?: boolean;
}

export interface CaptchaFixtureInit extends PageFixtureInit {
    form: FormFixture;
    pointer: PointerFixture;
    navigator: NavigatorFixture;
}

/**
 * Builds the flows and CAPTCHA stages the flow-executor tests run against.
 *
 * Every step drives the admin UI rather than the REST API, so a regression in the stage
 * form or the bind wizard surfaces here too.
 */
export class CaptchaFixture extends PageFixture {
    public static readonly fixtureName = "CAPTCHA";

    protected readonly form: FormFixture;
    protected readonly pointer: PointerFixture;
    protected readonly navigator: NavigatorFixture;

    constructor({ page, testName, form, pointer, navigator }: CaptchaFixtureInit) {
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
     * Create a CAPTCHA stage and bind it to a flow, through the flow's bind wizard.
     */
    public bindCaptchaStage = async ({
        flowSlug,
        vendor,
        name,
        order,
        interactive = true,
        autoSolve = false,
    }: BindCaptchaStageInit): Promise<void> => {
        const { page, pointer, navigator, form } = this;

        const { fill, setInputCheck } = form;

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

        await pointer.click("Create or bind...");
        await expect(wizard, "Bind wizard opens").toBeVisible({ timeout: 10_000 });

        await wizard.getByRole("radio", { name: "Captcha Stage" }).check();
        await page.getByTestId("wizard-navigation-next").click();

        const providerSelect = wizard.getByLabel("Provider Type");

        await expect(providerSelect, "Stage form is shown").toBeVisible();
        await providerSelect.selectOption({ label: vendor.providerType });

        await fill("Stage Name", name, wizard);
        const siteKey = autoSolve ? (vendor.autoSolveSiteKey ?? vendor.siteKey) : vendor.siteKey;

        await series(
            [fill, "Public Key", siteKey, wizard],
            [fill, "Secret Key", vendor.secretKey, wizard],
            [setInputCheck, "Interactive", interactive, wizard],
        );

        await page.getByTestId("wizard-navigation-next").click();

        // The wizard tries to back-fill the stage it just created, but the picker only holds
        // the first page of stages — in an environment where test stages have accumulated, a
        // brand-new stage falls outside it and the binding would save with a null stage.
        // Searching for it by name is both reliable and the path a user takes.
        const stageInput = wizard.getByRole("textbox", { name: "Stage" });

        await stageInput.click();
        await stageInput.fill(name);

        // The picker renders its options in a portal outside the wizard, so this is scoped to
        // the page. `.first()` because each option is a button with `role="option"` inside a
        // list item that carries the same role.
        const stageOption = page.getByRole("option", { name }).first();

        await expect(stageOption, "Created stage is offered by the picker").toBeVisible({
            timeout: 20_000,
        });

        await stageOption.click();

        // Filled after the stage, because adopting the stage re-renders this step and would
        // discard an order typed beforehand.
        await fill("Order", order.toString(), wizard);

        await page.getByTestId("wizard-navigation-next").click();

        await expect(wizard, "Bind wizard closes after save").toBeHidden({ timeout: 30_000 });

        this.logger.info(`Bound ${vendor.providerType} stage ${name} at order ${order}`);
    };

    /**
     * Open a flow in the flow executor.
     */
    public executeFlow = async (flowSlug: string): Promise<void> => {
        await this.navigator.navigate(`/if/flow/${flowSlug}/`);
    };

    /**
     * The stage element currently rendered by the flow executor.
     */
    public get stage() {
        return this.page.locator("ak-stage-captcha");
    }

    /**
     * The wrapper iframe the stage used to generate for every widget.
     *
     * Matched by the id the old implementation gave it. Vendors create srcless iframes of
     * their own, so the absence of *any* frame is not a usable signal — the absence of this
     * specific element is.
     */
    public get wrapperFrame() {
        return this.stage.locator("iframe#ak-captcha");
    }

    /**
     * Whether the page currently hosts a frame served by `vendor`.
     *
     * Every provider renders its challenge into an iframe of its own origin, which is the
     * most reliable signal of *which* vendor actually rendered. Read through
     * `page.frames()` rather than a DOM locator because Turnstile puts its iframe inside a
     * closed shadow root, where no selector can reach it.
     */
    public hasVendorFrame = (vendor: CaptchaVendorConfig): boolean => {
        return this.page.frames().some((frame) => frame.url().includes(vendor.widgetOrigin));
    };

    /**
     * The declared and rendered sizes of every vendor frame that sizes itself through
     * `width`/`height` content attributes.
     *
     * Empty for vendors that size their frame inline (Turnstile), or that render into a
     * closed shadow root where no selector can reach.
     */
    public declaredFrameSizes = (): Promise<
        Array<{ width: [declared: number, rendered: number]; height: [number, number] }>
    > => {
        return this.page.evaluate(() =>
            Array.from(
                document.querySelectorAll<HTMLIFrameElement>(
                    ".ak-captcha-container iframe[width][height]",
                ),
                (frame) => ({
                    width: [Number(frame.getAttribute("width")), frame.offsetWidth] as [
                        number,
                        number,
                    ],
                    height: [Number(frame.getAttribute("height")), frame.offsetHeight] as [
                        number,
                        number,
                    ],
                }),
            ),
        );
    };

    /**
     * Whether the vendor's script installed its global in the flow document's own realm.
     */
    public vendorGlobalDefined = (vendor: CaptchaVendorConfig): Promise<boolean> => {
        return this.page
            .evaluate(
                (globalName) => typeof (window as unknown as Record<string, unknown>)[globalName],
                vendor.globalName as string,
            )
            .then((type) => type !== "undefined");
    };

    /**
     * Complete the challenge the way a user would.
     */
    public solve = async (vendor: CaptchaVendorConfig): Promise<void> => {
        await this.expectVendorFrame(vendor);

        if (!vendor.requiresInteraction) return;

        // The checkbox lives in a cross-origin frame that can take a moment to paint after
        // the frame itself appears, so this waits for it rather than sampling once — a
        // silent no-op here reads as "the widget could not be solved", which is the exact
        // failure this suite exists to catch.
        const checkbox = async () => {
            for (const frame of this.page.frames()) {
                if (frame.isDetached() || !frame.url().includes(vendor.widgetOrigin)) continue;

                const candidate = frame.locator("#recaptcha-anchor, #checkbox").first();

                if (await candidate.isVisible().catch(() => false)) return candidate;
            }

            return null;
        };

        let target: Awaited<ReturnType<typeof checkbox>> = null;

        await expect
            .poll(async () => !!(target = await checkbox()), {
                message: `${vendor.providerType} renders a checkbox to click`,
                timeout: 20_000,
            })
            .toBe(true);

        // The vendor can tear the frame down mid-click once it solves.
        await target!.click().catch(() => undefined);
    };

    /**
     * Wait for `vendor` to have rendered its widget.
     */
    public expectVendorFrame = (vendor: CaptchaVendorConfig, present = true): Promise<void> => {
        const message = present
            ? `${vendor.providerType} renders its own frame`
            : `${vendor.providerType} has no frame on the page`;

        return expect
            .poll(() => this.hasVendorFrame(vendor), {
                message,
                // The vendor script is fetched over the network on first paint.
                timeout: 30_000,
            })
            .toBe(present);
    };
}
