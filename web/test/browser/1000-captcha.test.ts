import { expect, test } from "#e2e";
import { CAPTCHA_VENDORS, type CaptchaVendor } from "#e2e/fixtures/CaptchaFixture";

import { IDGenerator } from "@goauthentik/core/id";

/**
 * The CAPTCHA stage used to render each widget inside a generated `<iframe>` — a blob URL
 * or a `document.write`-populated `about:blank` document — purely so that two providers
 * could never collide over their `window` globals.
 *
 * These tests cover what replaced it: widgets render directly in the flow document, and
 * providers are chosen by the challenge's script URL rather than by whichever global
 * happens to be present.
 */

interface FlowNames {
    flowName: string;
    flowSlug: string;
    seed: string;
}

// Every case here loads a real vendor bundle from Google, hCaptcha or Cloudflare and, for
// the auto-solving keys, has authentik call the vendor's `siteverify` endpoint. That is the
// point — it is the only way to know the widgets actually work — but it makes the suite
// dependent on third-party availability, so CI excludes the tag and runs the
// provider-resolution unit tests instead.
test.describe("CAPTCHA stage", { tag: "@vendor-network" }, () => {
    const names = new Map<string, FlowNames>();

    test.beforeEach("Seed names", async ({ page: _page }, { testId }) => {
        const seed = IDGenerator.randomID(6).toLowerCase();

        names.set(testId, {
            seed,
            flowName: `Captcha Flow ${seed}`,
            flowSlug: `captcha-flow-${seed}`,
        });
    });

    for (const [key, vendor] of Object.entries(CAPTCHA_VENDORS) as [string, CaptchaVendor][]) {
        test(`Renders the ${vendor.providerType} widget without a wrapper iframe`, async ({
            session,
            captcha,
        }, testInfo) => {
            const { flowName, flowSlug } = names.get(testInfo.testId)!;

            await test.step("Authenticate", () => session.login({ to: "/if/admin/flow/flows" }));

            await test.step("Create the flow", () => captcha.createFlow(flowName, flowSlug));

            await test.step("Bind the CAPTCHA stage", () =>
                captcha.bindCaptchaStage({
                    flowSlug,
                    vendor,
                    name: `captcha-${key}-${flowSlug}`,
                    order: 0,
                }));

            await test.step("Execute the flow", () => captcha.executeFlow(flowSlug));

            await test.step("Vendor widget renders", () => captcha.expectVendorFrame(vendor));

            await test.step("Widget runs in the flow document", async () => {
                await expect(captcha.wrapperFrame, "Stage generates no wrapper iframe").toHaveCount(
                    0,
                );

                await expect(
                    await captcha.vendorGlobalDefined(vendor),
                    `\`window.${vendor.globalName}\` is defined in the flow document itself`,
                ).toBe(true);
            });
        });
    }

    // Non-interactive challenges never used the wrapper iframe, but they did render into a
    // container appended to `document.body`. They now share the interactive path's in-place
    // container, so they need covering too.
    test("Solves a non-interactive challenge without user input", async ({
        session,
        captcha,
        page,
    }, testInfo) => {
        const { flowName, flowSlug } = names.get(testInfo.testId)!;
        const vendor = CAPTCHA_VENDORS.turnstile;

        await test.step("Authenticate", () => session.login({ to: "/if/admin/flow/flows" }));

        await test.step("Create the flow", () => captcha.createFlow(flowName, flowSlug));

        await test.step("Bind an invisible CAPTCHA stage", () =>
            captcha.bindCaptchaStage({
                flowSlug,
                vendor,
                name: `captcha-invisible-${flowSlug}`,
                order: 0,
                interactive: false,
                autoSolve: true,
            }));

        await test.step("Execute the flow", () => captcha.executeFlow(flowSlug));

        await test.step("Flow completes on its own", async () => {
            await expect(page, "Flow advances past the CAPTCHA without user input").not.toHaveURL(
                new RegExp(`/if/flow/${flowSlug}`),
                { timeout: 30_000 },
            );
        });
    });

    // The reason the wrapper iframe existed: two stages using different providers load two
    // vendor scripts into one document, and both leave a global behind. Selecting a
    // controller by global returns whichever sorts first rather than the one this challenge
    // asked for, so the widget renders against the wrong site key.
    test("Renders the correct vendor when two providers share a document", async ({
        session,
        captcha,
        page,
    }, testInfo) => {
        const { flowName, flowSlug } = names.get(testInfo.testId)!;

        // Turnstile is first because it is the one vendor with a self-solving test key, so
        // the flow reaches the second stage without driving a click inside a cross-origin
        // vendor frame.
        const first = CAPTCHA_VENDORS.turnstile;
        const second = CAPTCHA_VENDORS.recaptcha;

        await test.step("Authenticate", () => session.login({ to: "/if/admin/flow/flows" }));

        await test.step("Create the flow", () => captcha.createFlow(flowName, flowSlug));

        await test.step("Bind the Turnstile stage", () =>
            captcha.bindCaptchaStage({
                flowSlug,
                vendor: first,
                name: `captcha-turnstile-${flowSlug}`,
                order: 0,
                autoSolve: true,
            }));

        await test.step("Bind the reCAPTCHA stage", () =>
            captcha.bindCaptchaStage({
                flowSlug,
                vendor: second,
                name: `captcha-recaptcha-${flowSlug}`,
                order: 10,
            }));

        await test.step("Execute the flow", () => captcha.executeFlow(flowSlug));

        await test.step("Second stage renders reCAPTCHA, not Turnstile", async () => {
            await captcha.expectVendorFrame(second);
            await captcha.expectVendorFrame(first, false);
        });

        await test.step("Both vendor globals are present", async () => {
            // The assertion that matters: the collision the wrapper iframe was hiding is
            // real and still happens — two globals do coexist — but selection no longer
            // depends on it.
            const globals = await page.evaluate(() => ({
                turnstile: typeof window.turnstile !== "undefined",
                grecaptcha: typeof window.grecaptcha !== "undefined",
            }));

            expect(globals, "Both providers' globals share the document").toEqual({
                turnstile: true,
                grecaptcha: true,
            });
        });

        await test.step("No wrapper iframe is created", async () => {
            await expect(captcha.wrapperFrame, "Stage generates no wrapper iframe").toHaveCount(0);
        });
    });
});
