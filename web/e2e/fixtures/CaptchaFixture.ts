import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PageFixture, PageFixtureInit } from "#e2e/fixtures/PageFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";

import { expect } from "@playwright/test";

/**
 * A CAPTCHA provider as the stage form offers it, paired with the vendor's published
 * always-pass test credentials.
 *
 * @remarks
 *
 * Every key below is documented by the vendor as a test credential and is safe to commit —
 * they are shared across every integrator and grant nothing. `siteKey` renders a widget
 * that solves without user input; `secretKey` makes the matching `siteverify` call succeed,
 * which is what lets the flow advance past the stage.
 *
 * @see {@link https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha-v2-what-should-i-do reCAPTCHA test keys}
 * @see {@link https://docs.hcaptcha.com/#integration-testing-test-keys hCaptcha test keys}
 * @see {@link https://developers.cloudflare.com/turnstile/troubleshooting/testing/ Turnstile test keys}
 */
export interface CaptchaVendor {
    /**
     * The label of the option in the stage form's "Provider Type" select.
     */
    providerType: string;
    /**
     * A site key whose widget waits for the user, so it stays on screen to be asserted
     * against.
     */
    siteKey: string;
    /**
     * A site key whose widget solves itself, used to advance a flow past this stage
     * without simulating a click inside a cross-origin vendor frame.
     *
     * Only needed where the vendor offers one; reCAPTCHA and hCaptcha always require a
     * click on their test keys.
     */
    autoSolveSiteKey?: string;
    secretKey: string;
    /**
     * The origin the vendor serves its widget iframe from, used to locate the rendered
     * widget without depending on vendor-specific markup.
     */
    widgetOrigin: string;
    /**
     * The global the vendor's script installs on `window`.
     */
    globalName: string;
}

export const CAPTCHA_VENDORS = {
    recaptcha: {
        providerType: "Google reCAPTCHA v2",
        siteKey: "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
        secretKey: "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe",
        widgetOrigin: "recaptcha.net",
        globalName: "grecaptcha",
    },
    hcaptcha: {
        providerType: "hCaptcha",
        // hCaptcha's "always passes" key solves with no interaction, completing the flow
        // before the widget can be asserted against. The bot-detected key renders the same
        // widget and never solves.
        siteKey: "30000000-ffff-ffff-ffff-000000000003",
        autoSolveSiteKey: "10000000-ffff-ffff-ffff-000000000001",
        secretKey: "0x0000000000000000000000000000000000000000",
        widgetOrigin: "hcaptcha.com",
        globalName: "hcaptcha",
    },
    turnstile: {
        providerType: "Cloudflare Turnstile",
        // Turnstile's "always passes" key solves with no interaction, which would complete
        // the flow before the widget could be asserted against. The forced-interactive key
        // renders the same widget but waits.
        siteKey: "3x00000000000000000000FF",
        autoSolveSiteKey: "1x00000000000000000000AA",
        secretKey: "1x0000000000000000000000000000000AA",
        widgetOrigin: "challenges.cloudflare.com",
        globalName: "turnstile",
    },
} as const satisfies Record<string, CaptchaVendor>;

export interface BindCaptchaStageInit {
    /**
     * The slug of the flow to bind the stage to.
     */
    flowSlug: string;
    vendor: CaptchaVendor;
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
    static fixtureName = "Captcha";

    readonly #form: FormFixture;
    readonly #pointer: PointerFixture;
    readonly #navigator: NavigatorFixture;

    constructor({ page, testName, form, pointer, navigator }: CaptchaFixtureInit) {
        super({ page, testName });

        this.#form = form;
        this.#pointer = pointer;
        this.#navigator = navigator;
    }

    /**
     * Create an empty authentication flow and return its slug.
     */
    public createFlow = async (name: string, slug: string): Promise<string> => {
        const { page } = this;

        await this.#navigator.navigate("/if/admin/flow/flows");

        const dialog = page.getByRole("dialog", { name: "New Flow" });

        await this.#pointer.click("New Flow");
        await expect(dialog, "Flow form opens").toBeVisible();

        await this.#form.fill("Flow Name", name, dialog);
        await this.#form.fill("Title", name, dialog);
        await this.#form.fill("Slug", slug, dialog);

        await dialog.getByLabel("Designation").selectOption("authentication");

        await this.#pointer.click("Create Flow", "button", dialog);

        // Every save here is a round-trip to one shared authentik instance that the other
        // workers are also writing to, so this is slower than a typical dialog dismissal.
        await expect(dialog, "Flow form closes after save").toBeHidden({ timeout: 30_000 });

        this.logger.info(`Created flow ${slug}`);

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
        const { page } = this;

        await this.#navigator.navigate(`/if/admin/flow/flows/${flowSlug}`);

        // The wizard relabels itself as it advances through its steps.
        const wizard = page.getByRole("dialog", {
            name: /New Stage Wizard|Create New Stage/,
        });

        // The bind wizard lives on the flow's "Stage Bindings" tab, not its overview.
        await page
            .getByRole("tab", { name: "Stage Bindings" })
            .or(page.getByRole("link", { name: "Stage Bindings" }))
            .click();

        await this.#pointer.click("Create or bind...");
        await expect(wizard, "Bind wizard opens").toBeVisible({ timeout: 10_000 });

        await wizard.getByRole("radio", { name: "Captcha Stage" }).check();
        await page.getByTestId("wizard-navigation-next").click();

        const providerSelect = wizard.getByLabel("Provider Type");

        await expect(providerSelect, "Stage form is shown").toBeVisible();
        await providerSelect.selectOption({ label: vendor.providerType });

        await this.#form.fill("Stage Name", name, wizard);
        const siteKey = autoSolve ? (vendor.autoSolveSiteKey ?? vendor.siteKey) : vendor.siteKey;

        await this.#form.fill("Public Key", siteKey, wizard);
        await this.#form.fill("Secret Key", vendor.secretKey, wizard);
        await this.#form.setInputCheck("Interactive", interactive, wizard);

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
        await this.#form.fill("Order", order.toString(), wizard);

        await page.getByTestId("wizard-navigation-next").click();

        await expect(wizard, "Bind wizard closes after save").toBeHidden({ timeout: 30_000 });

        this.logger.info(`Bound ${vendor.providerType} stage ${name} at order ${order}`);
    };

    /**
     * Open a flow in the flow executor.
     */
    public executeFlow = async (flowSlug: string): Promise<void> => {
        await this.#navigator.navigate(`/if/flow/${flowSlug}/`);
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
    public hasVendorFrame = (vendor: CaptchaVendor): boolean => {
        return this.page.frames().some((frame) => frame.url().includes(vendor.widgetOrigin));
    };

    /**
     * Whether the vendor's script installed its global in the flow document's own realm.
     *
     * This is the positive form of "no wrapper iframe": when the stage framed each widget,
     * the vendor script ran inside that frame and the top-level document never saw the
     * global at all.
     */
    public vendorGlobalDefined = (vendor: CaptchaVendor): Promise<boolean> => {
        return this.page
            .evaluate(
                (globalName) => typeof (window as unknown as Record<string, unknown>)[globalName],
                vendor.globalName,
            )
            .then((type) => type !== "undefined");
    };

    /**
     * Wait for `vendor` to have rendered its widget.
     */
    public expectVendorFrame = async (vendor: CaptchaVendor, present = true): Promise<void> => {
        await expect
            .poll(() => this.hasVendorFrame(vendor), {
                message: present
                    ? `${vendor.providerType} renders its own frame`
                    : `${vendor.providerType} has no frame on the page`,
                // The vendor script is fetched over the network on first paint.
                timeout: 30_000,
            })
            .toBe(present);
    };
}
