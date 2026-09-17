import "#admin/providers/scim/SCIMResourceTypesCard";
import type { SCIMResourceTypesCard } from "#admin/providers/scim/SCIMResourceTypesCard";

import {
    ProvidersApi,
    SCIMResourceTypeDiscovery,
    SCIMResourceTypeDiscoveryStatusEnum,
} from "@goauthentik/api";

import { afterEach, expect, test, vi } from "vitest";

const mounted: SCIMResourceTypesCard[] = [];

afterEach(() => {
    for (const card of mounted.splice(0)) card.remove();
    vi.restoreAllMocks();
});

async function mount() {
    const card = document.createElement("ak-provider-scim-resource-types");
    card.providerID = 1;
    document.body.append(card);
    mounted.push(card);
    await card.updateComplete;

    return card;
}

function result(
    status: SCIMResourceTypeDiscoveryStatusEnum = SCIMResourceTypeDiscoveryStatusEnum.Success,
): SCIMResourceTypeDiscovery {
    return {
        status,
        cached: true,
        fetchedAt: new Date("2026-09-17T12:00:00Z"),
        detail: "",
        resourceTypes: [],
    };
}

function button(card: SCIMResourceTypesCard) {
    return card.shadowRoot!.querySelector("button")!;
}

test("Fetches only on request and bypasses the cache when refreshed", async () => {
    const response = {
        ...result(),
        resourceTypes: [
            {
                id: "User",
                name: "User",
                endpoint: "/Users",
                schema: "urn:example:User",
                description: "User account",
                schemaExtensions: [{ schema: "urn:example:enterprise", required: true }],
            },
        ],
    };

    const fetch = vi
        .spyOn(ProvidersApi.prototype, "providersScimResourceTypesRetrieve")
        .mockResolvedValue(response);

    const card = await mount();
    expect(fetch).not.toHaveBeenCalled();
    expect(card.shadowRoot!.textContent).toContain("Not queried");
    button(card).click();
    await expect.poll(() => card.shadowRoot!.textContent).toContain("/Users");
    expect(fetch).toHaveBeenLastCalledWith({ id: 1, refresh: false });
    expect(card.shadowRoot!.textContent).toContain("(cached)");
    card.shadowRoot!.querySelector("summary")!.click();
    expect(card.shadowRoot!.querySelector("details")!.open).toBe(true);
    expect(card.shadowRoot!.textContent).toContain("urn:example:enterprise");
    expect(card.shadowRoot!.textContent).toContain("Required");
    button(card).click();
    await expect.poll(() => fetch.mock.calls.length).toBe(2);
    expect(fetch).toHaveBeenLastCalledWith({ id: 1, refresh: true });
});

test("Distinguishes an empty listing from unavailable discovery and failed requests", async () => {
    const fetch = vi
        .spyOn(ProvidersApi.prototype, "providersScimResourceTypesRetrieve")
        .mockResolvedValueOnce(result())
        .mockResolvedValueOnce({
            ...result(SCIMResourceTypeDiscoveryStatusEnum.Unavailable),
            detail: "ResourceTypes is unavailable (HTTP 404).",
        })
        .mockResolvedValueOnce({
            ...result(SCIMResourceTypeDiscoveryStatusEnum.Error),
            detail: "ResourceTypes request failed (HTTP 401).",
        })
        .mockRejectedValueOnce(new Error("API unavailable"));

    const card = await mount();
    button(card).click();
    await expect.poll(() => card.shadowRoot!.textContent).toContain("advertised no resource types");
    button(card).click();
    await expect.poll(() => card.shadowRoot!.textContent).toContain("HTTP 404");
    expect(card.shadowRoot!.textContent).not.toContain("advertised no resource types");
    button(card).click();
    await expect.poll(() => card.shadowRoot!.textContent).toContain("HTTP 401");
    button(card).click();
    await expect.poll(() => card.shadowRoot!.textContent).toContain("Unable to load");
    expect(button(card).disabled).toBe(false);
    expect(fetch).toHaveBeenCalledTimes(4);
});

test("Discards pending results when the selected provider changes", async () => {
    const pending = Promise.withResolvers<SCIMResourceTypeDiscovery>();

    const fetch = vi
        .spyOn(ProvidersApi.prototype, "providersScimResourceTypesRetrieve")
        .mockReturnValueOnce(pending.promise)
        .mockResolvedValueOnce(result());

    const card = await mount();
    button(card).click();
    await card.updateComplete;
    expect(button(card).disabled).toBe(true);
    card.providerID = 2;
    await card.updateComplete;
    pending.resolve({ ...result(), detail: "Old provider result" });
    await pending.promise;
    await card.updateComplete;
    expect(card.shadowRoot!.textContent).not.toContain("Old provider result");
    expect(card.shadowRoot!.textContent).toContain("Not queried");
    button(card).click();
    await expect.poll(() => card.shadowRoot!.textContent).toContain("advertised no resource types");
    expect(fetch).toHaveBeenLastCalledWith({ id: 2, refresh: false });
});
