import { expect, test } from "#e2e";
import { CaptchaVendorRecord } from "#e2e/fixtures/captcha-vendors";

import { IDGenerator } from "@goauthentik/core/id";

interface FlowNames {
    flowName: string;
    flowSlug: string;
    seed: string;
}

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

    for (const [key, vendor] of Object.entries(CaptchaVendorRecord)) {
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
                    captcha.vendorGlobalDefined(vendor),
                    `\`window.${vendor.globalName}\` is defined in the flow document itself`,
                ).resolves.toBe(true);
            });
        });
    }

    // The regression this suite originally missed: every case asserted that a widget
    // rendered, none that it could be solved. reCAPTCHA and hCaptcha rendered perfectly
    // while being impossible to complete, because they resolve their internals through
    // `document` and the container sat in the executor's shadow root.
    for (const [key, vendor] of Object.entries(CaptchaVendorRecord)) {
        test(`Solving the ${vendor.providerType} challenge advances the flow`, async ({
            session,
            captcha,
            page,
        }, testInfo) => {
            const { flowName, flowSlug } = names.get(testInfo.testId)!;

            await test.step("Authenticate", () => session.login({ to: "/if/admin/flow/flows" }));

            await test.step("Create the flow", () => captcha.createFlow(flowName, flowSlug));

            await test.step("Bind the CAPTCHA stage", () =>
                captcha.bindCaptchaStage({
                    flowSlug,
                    vendor,
                    name: `solve-${key}-${flowSlug}`,
                    order: 0,
                    // The passing key: this asserts a solved challenge is accepted, not how
                    // a vendor scores the client.
                    autoSolve: true,
                }));

            await test.step("Execute the flow", () => captcha.executeFlow(flowSlug));

            await test.step("Solve the challenge", () => captcha.solve(vendor));

            await test.step("Flow advances", async () => {
                await expect(page, "Flow leaves the CAPTCHA stage once solved").not.toHaveURL(
                    new RegExp(`/if/flow/${flowSlug}`),
                    { timeout: 30_000 },
                );
            });
        });
    }

    test("Solves a non-interactive challenge without user input", async ({
        session,
        captcha,
        page,
    }, testInfo) => {
        const { flowName, flowSlug } = names.get(testInfo.testId)!;
        const vendor = CaptchaVendorRecord.turnstile;

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

        // Turnstile is first because it is the one vendor with a self-solving test key.
        const first = CaptchaVendorRecord.turnstile;
        const second = CaptchaVendorRecord.recaptcha;

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
