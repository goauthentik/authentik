import "#components/ak-event-info";
import { EventInfo } from "./EventInfo.component";
import { fixtures } from "./EventInfo.fixtures";

import { createPaginatedResponse } from "#common/api/responses";
import { EventWithContext } from "#common/events";

import { FlowFromJSON, FlowsApi } from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";

const mounted = new Set<HTMLElement>();

async function mount(event?: EventWithContext): Promise<EventInfo> {
    const element = new EventInfo();

    if (event) element.event = event;
    document.body.appendChild(element);
    mounted.add(element);
    await element.updateComplete;

    return element;
}

const $ = (element: EventInfo, selector: string) =>
    element.renderRoot.querySelector<HTMLElement>(selector);

const text = (element: EventInfo) => element.renderRoot.textContent?.replace(/\s+/g, " ") ?? "";

afterEach(() => {
    mounted.forEach((element) => element.remove());
    mounted.clear();
    vi.restoreAllMocks();
});

describe("ak-event-info", () => {
    it("shows a spinner until an event is set", async () => {
        const element = await mount();
        expect($(element, "ak-spinner")).not.toBeNull();
    });

    describe.each([
        ["modelCreated", ["Affected model:", "Password", "passworddevice"]],
        ["modelUpdated", ["Changes made:", '"old"', '"new"']],
        ["modelUpdatedM2M", ["Added ID 3", "Added ID 5", "Removed ID 9", "Cleared"]],
        ["modelDeleted", ["Affected model:", "Doomed!"]],
        ["emailSent", ["Email info:", "A mighty subject", "guests@mighty.authentik.io"]],
        ["secretView", ["Secret:", "439ac0de", "ifyoucanreadthisyouresittingtooclose"]],
        ["systemException", ["Open issue on GitHub...", "KeyError: 'brains'"]],
        ["systemTaskException", ["Exception", "apply_blueprint encountered an error"]],
        ["configurationWarning", ["Warning! Brains!"]],
        ["configurationError", ["Error! Missing Brains!"]],
        ["updateAvailable", ["New version available", "666.6.6"]],
        ["loginFailed", ["Attempted to log in as j-random-hacker"]],
        ["logout", ["No additional data available."]],
        ["propertyMappingException", ["Exception", "Expression", "request.user.name"]],
        ["policyException", ["Binding", "require-brains", "Policy failed to execute"]],
        ["policyExecution", ["Result", "Passing: true"]],
        ["policyExecutionDryRun", ["Dry-run", "Brains required.", "Raw result", "Cached: No"]],
    ] as const)("%s", (name, expected) => {
        it("renders its distinguishing content", async () => {
            const element = await mount(fixtures[name]);
            const content = text(element);

            for (const fragment of expected) expect(content).toContain(fragment);
        });
    });

    // Renderers that intentionally have no raw Context/User expand.
    it.each(["secretView", "systemTaskException", "updateAvailable", "logout"] as const)(
        "%s has no raw-data expand",
        async (name) => {
            const element = await mount(fixtures[name]);
            expect($(element, "ak-attribute-view")).toBeNull();
        },
    );

    it.each(["login", "logoutWithContext", "unhandled"] as const)(
        "%s falls through to the default context/user view",
        async (name) => {
            const element = await mount(fixtures[name]);
            expect(element.renderRoot.querySelectorAll("ak-attribute-view")).toHaveLength(2);
            expect($(element, "ak-expand")).toBeNull();
        },
    );

    it("resolves the flow link for an authorized application", async () => {
        const flow = FlowFromJSON({ slug: "default-provider-authorization", name: "Authorize" });

        const list = vi
            .spyOn(FlowsApi.prototype, "flowsInstancesList")
            .mockResolvedValue({ ...createPaginatedResponse([flow]), autocomplete: {} });

        const element = await mount(fixtures.authorizeApplication);

        expect(list).toHaveBeenCalledWith({ flowUuid: fixtures.authorizeApplication.context.flow });
        expect(text(element)).toContain("Brain Bank");

        await vi.waitFor(() =>
            expect($(element, `a[href$="flow/flows/${flow.slug}"]`)).not.toBeNull(),
        );
    });

    it("links the update to the changelog, or to the release tag without one", async () => {
        const withChangelog = await mount(fixtures.updateAvailable);

        expect($(withChangelog, "a")?.getAttribute("href")).toBe(
            fixtures.updateAvailable.context.changelog,
        );

        const { changelog: _, ...context } = fixtures.updateAvailable.context;
        const withoutChangelog = await mount({ ...fixtures.updateAvailable, context });

        expect($(withoutChangelog, "a")?.getAttribute("href")).toBe(
            "https://github.com/goauthentik/authentik/releases/tag/version%2F666.6.6",
        );
    });

    it("titles the GitHub issue with the failing request", async () => {
        const element = await mount(fixtures.systemException);
        const href = $(element, "a.pf-c-button")?.getAttribute("href") ?? "";
        expect(href).toMatch(/^https:\/\/github\.com\/goauthentik\/authentik\/issues\/new/);
        expect(href).toContain(`&title=${encodeURIComponent("GET /api/v3/core/users/")}`);
    });

    it("replaces the inline logo reference in sent email bodies", async () => {
        const element = await mount(fixtures.emailSent);
        const srcdoc = $(element, "iframe")?.getAttribute("srcdoc") ?? "";
        expect(srcdoc).toContain("icon_left_brand.png");
        expect(srcdoc).not.toContain("cid:logo");
    });

    it("omits the dry-run label and cache status on a live execution", async () => {
        const element = await mount(fixtures.policyExecution);
        expect($(element, "ak-label")).toBeNull();
        expect(text(element)).not.toContain("Cached");
    });

    // The server records the login source under PLAN_CONTEXT_SOURCE, which is `source`.
    it("shows the source used to log in", async () => {
        const element = await mount(fixtures.loginWithSource);
        expect(text(element)).toContain("Using source");
        expect(text(element)).toContain("GitHub");
    });

    // Known bug: M2M diff entries carry no `previous_value`, so `undefined !== null` passes and
    // JSON.stringify(undefined) renders an empty cell instead of "-".
    it.fails("shows '-' as the previous value of an M2M change", async () => {
        const element = await mount(fixtures.modelUpdatedM2M);
        const cells = [...element.renderRoot.querySelectorAll("tbody tr td:nth-child(2)")];

        for (const cell of cells) expect(cell.textContent?.trim()).toBe("-");
    });
});
