import { PageFixture, PageFixtureInit } from "#e2e/fixtures/PageFixture";

import { BrowserContext } from "@playwright/test";

export interface PasskeyFixtureInit extends PageFixtureInit {
    context: BrowserContext;
}

export interface PasskeyQuery {
    /**
     * Relying party id to filter by — for authentik, the host the flow runs on.
     */
    rpId?: string;
    /**
     * Base64url-encoded credential id to filter by.
     */
    id?: string;
}

/**
 * Drives Playwright's virtual WebAuthn authenticator.
 *
 * A real ceremony needs hardware and a human touching it, neither of which exists in CI.
 * The virtual authenticator answers `navigator.credentials.create()` and
 * `navigator.credentials.get()` in-browser with a software keypair, so registration and
 * login flows run end-to-end against a real authentik instance without either.
 *
 * @see {@link https://playwright.dev/docs/api/class-credentials | Playwright Credentials}
 */
export class PasskeyFixture extends PageFixture {
    static fixtureName = "Passkey";

    protected readonly context: BrowserContext;

    #installed = false;

    constructor({ page, testName, context }: PasskeyFixtureInit) {
        super({ page, testName });

        this.context = context;
    }

    /**
     * Install the virtual authenticator into the browser context.
     *
     * Must be called **before** navigating to a page that runs a ceremony — the override is
     * injected at document start, so a page that has already loaded keeps the real
     * `navigator.credentials`. Calling this more than once is a no-op.
     */
    public install = async (): Promise<void> => {
        if (this.#installed) return;

        this.logger.info("Installing virtual WebAuthn authenticator...");

        await this.context.credentials.install();

        this.#installed = true;
    };

    /**
     * Seed a discoverable credential without running a registration ceremony.
     *
     * Only useful when the server already knows the credential — for a fresh device, register
     * through the UI instead so authentik records the device too.
     */
    public seed = async (rpId: string): Promise<string> => {
        await this.install();

        this.logger.info(`Seeding a credential for ${rpId}...`);

        const { id } = await this.context.credentials.create(rpId);

        return id;
    };

    /**
     * The credentials the virtual authenticator currently holds.
     */
    public credentials = (query?: PasskeyQuery) => this.context.credentials.get(query);
}
