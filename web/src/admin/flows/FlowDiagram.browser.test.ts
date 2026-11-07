import "#admin/flows/FlowDiagram";
import { FlowDiagram } from "#admin/flows/FlowDiagram";

import { FlowsApi, ResponseError } from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
});

describe("Flow diagram", () => {
    it("shows the error instead of the loading placeholder when the diagram fails to load", async () => {
        vi.spyOn(FlowsApi.prototype, "flowsInstancesDiagramRetrieve").mockRejectedValue(
            new ResponseError(
                Response.json({ detail: "Not found." }, { status: 404, statusText: "Not Found" }),
            ),
        );

        const diagram = document.body.appendChild(new FlowDiagram());
        diagram.flowSlug = "missing";

        await vi.waitFor(() => {
            const state = diagram.renderRoot.querySelector("ak-empty-state");

            expect(state?.loading).toBe(false);
            expect(state?.textContent).toContain("Not found.");
        });
    });
});
