import "#admin/flows/FlowViewPage";
import "#elements/router/core/RouterView";
import { createPaginatedResponse } from "#common/api/responses";
import { AKRefreshEvent } from "#common/events";

import { initRouter, resetRouterConfig } from "#elements/router/core/config";
import { formatInterfacePrefix } from "#elements/router/core/interfaces";

import { FlowDiagram } from "#admin/flows/FlowDiagram";
import { FlowViewPage } from "#admin/flows/FlowViewPage";
import { ROUTES } from "#admin/Routes";

import {
    DiagramNodeTypeEnum,
    Flow,
    FlowDiagramFromJSON,
    FlowFromJSON,
    FlowsApi,
    ResponseError,
} from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { html, render } from "lit";

// Mermaid's first render can take over a second under full-suite load.
const waitForRender = { timeout: 5000 } as const;

const FLOW_PK = "8f6d1c3e-0000-4000-8000-000000000001";

const flowFixture = (slug: string, name = "Login") =>
    FlowFromJSON({
        pk: FLOW_PK,
        policybindingmodel_ptr_id: "8f6d1c3e-0000-4000-8000-000000000002",
        name,
        slug,
        title: "Welcome",
        designation: "authentication",
        export_url: `/api/v3/flows/instances/${slug}/export/`,
    });

const notFound = () =>
    new ResponseError(
        Response.json({ detail: "Not found." }, { status: 404, statusText: "Not Found" }),
    );

/**
 * Serve `flow` and its diagram by slug, as the API does, and 404 every other slug.
 */
function serveFlow(flow: Flow) {
    vi.spyOn(FlowsApi.prototype, "flowsInstancesRetrieve").mockImplementation(async ({ slug }) => {
        if (slug === flow.slug) return flow;

        throw notFound();
    });

    vi.spyOn(FlowsApi.prototype, "flowsInstancesDiagramRetrieve").mockImplementation(
        async ({ slug }) => {
            if (slug !== flow.slug) throw notFound();

            return FlowDiagramFromJSON({
                nodes: [
                    {
                        identifier: "flow_start",
                        type: DiagramNodeTypeEnum.FlowStart,
                        name: `${flow.name} graph`,
                        verbose_name: "Flow",
                        model: "",
                        pk: "",
                        component: "",
                        binding_model: "",
                        binding_pk: "",
                        binding_order: null,
                    },
                ],
                edges: [],
            });
        },
    );

    return vi
        .spyOn(FlowsApi.prototype, "flowsInstancesList")
        .mockResolvedValue(createPaginatedResponse([flow]));
}

const container = document.createElement("div");

/**
 * Open the flow page through the admin interface's router, as a user would.
 */
function openFlowPage(slug: string): void {
    history.replaceState(null, "", `/if/admin/flow/flows/${slug}`);
    document.body.append(container);

    render(
        html`<ak-router-view
            .routes=${ROUTES}
            .prefix=${formatInterfacePrefix("/", "admin")}
        ></ak-router-view>`,
        container,
    );
}

/**
 * The mounted flow page and its diagram, once the diagram shows `graphName`.
 */
function renderedPage(graphName: string): Promise<[FlowViewPage, FlowDiagram]> {
    return vi.waitFor(() => {
        const page = container
            .querySelector("ak-router-view")
            ?.renderRoot.querySelector("ak-flow-view");

        const diagram = page?.renderRoot.querySelector("ak-flow-diagram");

        expect(diagram?.renderRoot.querySelector("svg")?.textContent).toContain(graphName);

        return [page!, diagram!];
    }, waitForRender);
}

/**
 * Report a saved edit the way the Edit button's dialog does.
 */
function saveEdit(page: FlowViewPage): void {
    const editButton = [...page.renderRoot.querySelectorAll("button")].find(
        (button) => button.textContent?.trim() === "Edit",
    );

    editButton!.dispatchEvent(new AKRefreshEvent());
}

beforeEach(() => {
    initRouter({ base: "/", interfaceName: "admin" });
});

afterEach(() => {
    render(null, container);
    container.remove();
    resetRouterConfig();
    history.replaceState(null, "", "/");
    vi.restoreAllMocks();
});

describe("Flow page", () => {
    it("shows an edit without clearing the diagram", async () => {
        serveFlow(flowFixture("login"));
        openFlowPage("login");

        const [page, diagram] = await renderedPage("Login graph");

        serveFlow(flowFixture("login", "Sign in"));
        saveEdit(page);

        // The diagram keeps showing while its refresh runs.
        expect(diagram.diagram).not.toBe("");

        await vi.waitFor(() => expect(page.renderRoot.textContent).toContain("Sign in"));
        await renderedPage("Sign in graph");
    });

    it("moves to the new URL after the slug is edited", async () => {
        serveFlow(flowFixture("login"));
        openFlowPage("login");

        const [page] = await renderedPage("Login graph");
        const historyLength = history.length;

        const list = serveFlow(flowFixture("sign-in", "Renamed"));
        saveEdit(page);

        const [nextPage] = await renderedPage("Renamed graph");

        expect(list).toHaveBeenCalledExactlyOnceWith({ flowUuid: FLOW_PK });
        expect(window.location.pathname).toBe("/if/admin/flow/flows/sign-in");
        expect(history.length).toBe(historyLength);
        expect(nextPage.renderRoot.querySelector("code")?.textContent).toBe("sign-in");
    });
});
