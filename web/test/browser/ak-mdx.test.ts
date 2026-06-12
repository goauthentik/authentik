import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

/**
 * `<ak-mdx>` renders the OAuth 2.0 provider docs (`oauth2/index.mdx`) on
 * the OAuth2 provider view page. That document is well-suited to exercise
 * the full pipeline because it contains:
 *
 * - frontmatter (`title: OAuth 2.0 provider`)
 * - multiple H2 headings (id slugs)
 * - `:::caution` and `:::info` admonitions (two flavours: with title, without)
 * - relative-doc links (`./create-oauth2-provider.md`)
 * - external links (`https://oauth.net/2/`)
 * - a `mermaid` sequence diagram
 *
 * These tests boot the admin UI, create a fresh OAuth2 provider, navigate
 * to its view page, and then assert against the rendered DOM inside
 * `<ak-mdx>`'s shadow root.
 */
test.describe("ak-mdx renders compiled markdown", () => {
    let providerName: string;

    test.beforeEach("Provision an OAuth2 provider", async ({ session, form, pointer, page }) => {
        const seed = IDGenerator.randomID(6);
        providerName = `${randomName(seed)} (${seed})`;

        const { fill, selectSearchValue } = form;
        const { click } = pointer;

        await test.step("Authenticate", () => session.login({ to: "/if/admin/#/core/providers" }));

        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await test.step("Create provider via wizard", async () => {
            await expect(dialog).toBeHidden();
            await page.getByRole("button", { name: "New Provider" }).click();
            await expect(dialog).toBeVisible();

            await series(
                [click, "OAuth2/OpenID", "option"],
                [fill, "Provider Name", providerName],
                [
                    selectSearchValue,
                    "Authorization Flow",
                    /default-provider-authorization-explicit-consent/,
                ],
                [click, "Create", "button", dialog],
            );

            await expect(dialog).toBeHidden();
        });

        await test.step("Navigate to the provider's view page", async () => {
            const $row = await form.search(providerName);
            // The provider name cell is a link that opens the view page.
            await $row.getByRole("link", { name: providerName }).first().click();
        });
    });

    /**
     * @returns a Locator scoped to the rendered `<ak-mdx>` element on the
     * provider view page (there is exactly one inside the docs card).
     */
    const $mdx = (page: import("@playwright/test").Page) =>
        page.locator("ak-mdx").filter({ has: page.locator('h1[part="title"]') });

    test("frontmatter title and heading slugs are rendered", async ({ page }) => {
        const mdx = $mdx(page);

        await expect(
            mdx.locator('h1[part="title"]'),
            "Frontmatter `title` rendered as an `<h1 part=title>`",
        ).toHaveText("OAuth 2.0 provider");

        await expect(
            mdx.locator("h2#authentik-and-oauth-2-0"),
            "H2 carries a kebab-cased id slug derived from its text",
        ).toBeVisible();

        await expect(
            mdx.locator("h2#about-oauth-2-0-and-oidc"),
            "Multiple H2s each receive their own slug",
        ).toBeVisible();
    });

    test("admonitions render as <ak-alert> with the right level", async ({ page }) => {
        const mdx = $mdx(page);

        const $caution = mdx
            .locator('ak-alert[level="pf-m-warning"]')
            .filter({ hasText: "Reserved application slugs" });
        await expect(
            $caution,
            "`:::caution Title` renders an `<ak-alert level=pf-m-warning>` with the title in `<strong>`",
        ).toBeVisible();
        await expect(
            $caution.locator("strong"),
            "Bare-space directive label is promoted to `<strong>`",
        ).toHaveText("Reserved application slugs");

        await expect(
            mdx.locator('ak-alert[level="pf-m-info"]').first(),
            "`:::info` blocks render as `<ak-alert level=pf-m-info>`",
        ).toBeVisible();
    });

    test("links are wrapped in <ak-md-a> with build-time URL resolution", async ({ page }) => {
        const mdx = $mdx(page);

        const $external = mdx.locator('ak-md-a > a[href="https://oauth.net/2/"]');
        await expect($external, "External link preserved verbatim").toBeVisible();
        await expect($external).toHaveAttribute("target", "_blank");
        await expect($external).toHaveAttribute("rel", "noopener noreferrer");

        const $relative = mdx
            .locator('ak-md-a > a[href*="next.goauthentik.io"][href*="create-oauth2-provider"]')
            .first();
        await expect(
            $relative,
            "Relative `./create-oauth2-provider.md` resolved to docs site URL at build time",
        ).toBeVisible();
        await expect($relative).toHaveAttribute("target", "_blank");

        // Fragment href is preserved verbatim from the source markdown,
        // even when (as here) the docs author's intended target slug
        // doesn't match this pipeline's slug algorithm. The wrapper
        // intercepts the click regardless — the lookup only fails the
        // scroll, not the link itself.
        const $fragment = mdx.locator('ak-md-a > a[href="#about-oauth-20-and-oidc"]').first();
        await expect(
            $fragment,
            "Fragment links are kept as `#…` so the wrapper can intercept them",
        ).toBeVisible();
        await expect(
            $fragment,
            "Fragment links do NOT receive `target=_blank`",
        ).not.toHaveAttribute("target", "_blank");
    });

    test("mermaid diagrams render via <ak-diagram>", async ({ page }) => {
        const mdx = $mdx(page);

        const $diagram = mdx.locator("ak-diagram").first();
        await expect($diagram).toBeVisible();

        const $svg = $diagram.locator("svg");
        await expect(
            $svg,
            "<ak-diagram> resolves the mermaid SVG into its shadow root",
        ).toBeVisible({ timeout: 10_000 });
    });

    test("mermaid responds to theme changes", async ({ page }) => {
        const mdx = $mdx(page);
        const $svg = mdx.locator("ak-diagram svg").first();
        await expect($svg).toBeVisible({ timeout: 10_000 });

        // `<ak-diagram>` re-renders the whole SVG via `mermaid.render(...)` on
        // every `AKMermaidRefreshEvent`. Mermaid bakes the active theme into
        // an inline `<style>` block inside the SVG, so the easiest stable
        // signal that the right theme was applied is to assert the
        // serialized SVG content changes between toggles.
        const captureSVG = () => $svg.evaluate((el) => el.outerHTML);
        const darkSVG = await captureSVG();
        expect(darkSVG.length, "Initial mermaid SVG is non-empty").toBeGreaterThan(0);

        await test.step("Toggle to light theme", async () => {
            await page.evaluate(() => {
                document.documentElement.dataset.themeChoice = "light";
            });
        });

        await expect
            .poll(captureSVG, {
                message: "SVG content should change when re-rendered for light theme",
                timeout: 10_000,
            })
            .not.toBe(darkSVG);

        const lightSVG = await captureSVG();

        await test.step("Toggle back to dark theme", async () => {
            await page.evaluate(() => {
                document.documentElement.dataset.themeChoice = "dark";
            });
        });

        await expect
            .poll(captureSVG, {
                message: "SVG content should change again when re-rendered for dark theme",
                timeout: 10_000,
            })
            .not.toBe(lightSVG);
    });
});
