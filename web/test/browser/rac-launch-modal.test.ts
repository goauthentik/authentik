/**
 * @file Regression test for the RAC endpoint picker modal.
 *
 * Covers a 2026.5 RC regression: opening the RAC application from the user
 * library rendered an empty endpoint list until the user manually clicked
 * the refresh button. Root cause was that `AKModal` force-sets
 * `visible = true` on its slotted child before that child's first update
 * cycle, which short-circuited `Table`'s deferred-refresh state machine so
 * no initial `fetch()` ever fired.
 */

import { expect, test } from "#e2e";

import { IDGenerator } from "@goauthentik/core/id";

const ADMIN_TOKEN = process.env.AK_TEST_BOOTSTRAP_TOKEN ?? "playpen-dev-bootstrap-token-changeme";
const AUTHORIZATION_FLOW_SLUG = "default-provider-authorization-explicit-consent";

interface APIClient {
    post(path: string, body: unknown): Promise<Record<string, unknown>>;
    get(path: string): Promise<Record<string, unknown>>;
    delete(path: string): Promise<void>;
}

function makeAPIClient(baseURL: string, token: string, request: typeof fetch): APIClient {
    const headers = {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
        "Accept": "application/json",
    };

    const handle = async (response: Response): Promise<Record<string, unknown>> => {
        const text = await response.text();

        if (!response.ok) {
            throw new Error(
                `API ${response.status} ${response.statusText} for ${response.url}: ${text}`,
            );
        }

        return text ? (JSON.parse(text) as Record<string, unknown>) : {};
    };

    return {
        async post(path, body) {
            return handle(
                await request(`${baseURL}${path}`, {
                    method: "POST",
                    headers,
                    body: JSON.stringify(body),
                }),
            );
        },
        async get(path) {
            return handle(
                await request(`${baseURL}${path}`, {
                    method: "GET",
                    headers,
                }),
            );
        },
        async delete(path) {
            const response = await request(`${baseURL}${path}`, {
                method: "DELETE",
                headers,
            });

            if (!response.ok && response.status !== 404) {
                throw new Error(
                    `API ${response.status} ${response.statusText} for ${response.url}`,
                );
            }
        },
    };
}

test.describe("RAC endpoint launch modal", () => {
    test("populates endpoints on open without a manual refresh", async ({
        session,
        page,
        baseURL,
    }) => {
        const seed = IDGenerator.randomID(6);
        const providerName = `rac-launch-modal-${seed}`;
        const appSlug = `rac-launch-modal-${seed}`;
        const endpoint1Name = `rac-endpoint-${seed}-a`;
        const endpoint2Name = `rac-endpoint-${seed}-b`;

        const api = makeAPIClient(baseURL!, ADMIN_TOKEN, fetch);

        let providerPk: number | null = null;
        let appUUID: string | null = null;

        try {
            await test.step("Seed RAC provider + endpoints + application", async () => {
                const flows = (await api.get(
                    `/api/v3/flows/instances/?slug=${AUTHORIZATION_FLOW_SLUG}`,
                )) as { results: Array<{ pk: string }> };

                const flowPk = flows.results?.[0]?.pk;

                expect(flowPk, "Authorization flow exists").toBeTruthy();

                const provider = (await api.post("/api/v3/providers/rac/", {
                    name: providerName,
                    authorization_flow: flowPk,
                    connection_expiry: "hours=8",
                })) as { pk: number };

                providerPk = provider.pk;

                // Two endpoints, so the modal stays open instead of auto-launching
                // the only one (see RACLaunchEndpointLaunch.apiEndpoint()).
                await api.post("/api/v3/rac/endpoints/", {
                    name: endpoint1Name,
                    provider: providerPk,
                    host: "localhost:5900",
                    protocol: "vnc",
                    auth_mode: "prompt",
                });

                await api.post("/api/v3/rac/endpoints/", {
                    name: endpoint2Name,
                    provider: providerPk,
                    host: "localhost:5901",
                    protocol: "vnc",
                    auth_mode: "prompt",
                });

                const app = (await api.post("/api/v3/core/applications/", {
                    name: providerName,
                    slug: appSlug,
                    provider: providerPk,
                })) as { pk: string };

                appUUID = app.pk;
            });

            const endpointListRequests: string[] = [];
            page.on("request", (request) => {
                if (request.url().includes("/api/v3/rac/endpoints/")) {
                    endpointListRequests.push(request.url());
                }
            });

            await test.step("Authenticate and navigate to the user library", async () => {
                await session.login({ to: "/if/user/" });
            });

            const appCard = page.locator(`[data-application-name="${appSlug}"]`);

            await expect(appCard, "Application card is visible").toBeVisible();

            await test.step("Open the endpoint launcher", async () => {
                await appCard.getByRole("button", { name: `Open "${providerName}"` }).click();
            });

            const dialog = page.getByRole("dialog", { name: /Launch Endpoint/i });

            await expect(dialog, "Endpoint launcher dialog opens").toBeVisible();

            await test.step("Endpoint list populates without manual refresh", async () => {
                await expect(
                    dialog.getByRole("cell", { name: endpoint1Name }),
                    "First endpoint row is visible without a manual refresh",
                ).toBeVisible({ timeout: 5_000 });

                await expect(
                    dialog.getByRole("cell", { name: endpoint2Name }),
                    "Second endpoint row is visible without a manual refresh",
                ).toBeVisible();

                expect(
                    endpointListRequests.length,
                    "Modal-open triggers at least one endpoints list fetch",
                ).toBeGreaterThanOrEqual(1);
            });
        } finally {
            if (appUUID) await api.delete(`/api/v3/core/applications/${appSlug}/`);
            if (providerPk !== null) await api.delete(`/api/v3/providers/rac/${providerPk}/`);
        }
    });
});
