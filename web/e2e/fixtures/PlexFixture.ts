import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PageFixture, PageFixtureInit } from "#e2e/fixtures/PageFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { series } from "#packages/core/promises";

import { expect, Page } from "@playwright/test";

/**
 * A plex.tv account the suite signs in with.
 */
export interface PlexCredentials {
    email: string;
    password: string;
}

/**
 * The plex.tv account from `AK_TEST_PLEX_EMAIL` and `AK_TEST_PLEX_PASSWORD`, or `null` when
 * either is unset — which is what keeps the Plex suite from running by default.
 */
export function plexCredentials(): PlexCredentials | null {
    const email = process.env.AK_TEST_PLEX_EMAIL;
    const password = process.env.AK_TEST_PLEX_PASSWORD;

    return email && password ? { email, password } : null;
}

export interface CreatePlexSourceInit {
    name: string;
    slug: string;
}

export interface PlexFixtureInit extends PageFixtureInit {
    form: FormFixture;
    pointer: PointerFixture;
    navigator: NavigatorFixture;
}

/**
 * Creates Plex sources through the admin UI, and signs in on app.plex.tv.
 *
 * Talks to the real plex.tv: the token a source redeems is checked server-side against
 * plex.tv, so there is nothing to intercept in the browser.
 */
export class PlexFixture extends PageFixture {
    public static readonly fixtureName = "Plex";

    protected readonly form: FormFixture;
    protected readonly pointer: PointerFixture;
    protected readonly navigator: NavigatorFixture;

    constructor({ page, testName, form, pointer, navigator }: PlexFixtureInit) {
        super({ page, testName });

        this.form = form;
        this.pointer = pointer;
        this.navigator = navigator;
    }

    /**
     * Create a Plex source from the New Source wizard.
     *
     * "Load servers" signs in to plex.tv in a popup. The account that signs in becomes the
     * source's token owner, and with friends allowed (the default) the owner may sign in
     * through the source without sharing a server.
     */
    public createSource = async ({ name, slug }: CreatePlexSourceInit): Promise<void> => {
        const { page, form, pointer, navigator, logger } = this;
        const { fill, setInputCheck } = form;

        await navigator.navigate("/if/admin/core/sources");

        const dialog = page.getByRole("dialog", { name: /New Source/ });

        // An empty table repeats the button in its empty state, so target the toolbar's.
        await pointer.click("New Source", "button", page.getByRole("toolbar"));
        await expect(dialog, "Source wizard opens").toBeVisible();

        await pointer.click(/^Plex/, "option", dialog);

        await series([fill, "Source Name", name, dialog], [fill, "Slug", slug, dialog]);

        // Every run makes a new source, but signs in with the same Plex account. Linking by
        // username lets a rerun adopt the user an earlier run enrolled, instead of failing
        // to create a second user with the same username.
        //
        // The select has no accessible name; the user matching mode is the only one that
        // offers username linking.
        await dialog
            .getByRole("combobox")
            .filter({ has: page.getByRole("option", { name: /identical username/ }) })
            .selectOption("username_link");

        // The popup has to open inside the click, or the browser blocks it.
        const [popup] = await Promise.all([
            page.waitForEvent("popup"),
            pointer.click("Load servers", "button", dialog),
        ]);

        await this.signIn(popup);

        await expect
            .poll(() => popup.isClosed(), {
                message: "Popup closes once Plex authorizes the pin",
                timeout: 30_000,
            })
            .toBe(true);

        await expect(
            dialog.getByRole("button", { name: "Re-authenticate with Plex" }),
            "Form holds a Plex token",
        ).toBeVisible({ timeout: 15_000 });

        await setInputCheck(
            "Allow friends to authenticate via Plex, even if you don't share any servers",
            true,
            dialog,
        );

        await pointer.click("Create", "button", dialog);

        await expect(dialog, "Source wizard closes after save").toBeHidden({ timeout: 30_000 });

        logger.info(`Created Plex source ${slug}`);
    };

    /**
     * Sign in on an app.plex.tv auth page, in whichever state plex.tv presents it.
     *
     * A browser without a plex.tv session gets the login form; one with a session gets a
     * single "Sign In" button that approves the pin.
     */
    public signIn = async (page: Page): Promise<void> => {
        const credentials = plexCredentials();

        if (!credentials) {
            throw new Error("Set AK_TEST_PLEX_EMAIL and AK_TEST_PLEX_PASSWORD to sign in to Plex");
        }

        // The whole auth UI renders in an iframe on app.plex.tv.
        const frame = page.frameLocator('iframe[src*="/auth-form/"]');

        const emailOption = frame.getByRole("button", { name: "Continue with Email" });
        const approve = frame.getByRole("button", { name: "Sign In" });

        await expect(emailOption.or(approve), "Plex auth page loads").toBeVisible({
            timeout: 30_000,
        });

        if (await emailOption.isVisible()) {
            await emailOption.click();

            const passwordField = frame.getByRole("textbox", { name: "Password" });

            await frame.getByRole("textbox", { name: "Email or Username" }).fill(credentials.email);
            await passwordField.fill(credentials.password);
            await approve.click();

            // Plex may still ask to approve the pin once signed in. The login form's own
            // "Sign In" button shares the name, so wait for the form to go first.
            const leftForm = await passwordField
                .waitFor({ state: "detached", timeout: 30_000 })
                .then(() => true)
                .catch(() => page.isClosed());

            if (!leftForm || page.isClosed()) return;
        }

        const approval = await approve
            .waitFor({ timeout: 10_000 })
            .then(() => true)
            .catch(() => false);

        if (approval && !page.isClosed()) {
            await approve.click();
        }
    };
}
