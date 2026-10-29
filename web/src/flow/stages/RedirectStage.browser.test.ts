import { injectBrand } from "#common/brand";

import { RedirectStage } from "#flow/stages/RedirectStage";
import { Broadcast } from "#flow/tabs/broadcast";

import { RedirectChallenge } from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// The same-origin re-entry an SP-initiated SAML login redirects to once authentication is done.
const resumeURL = "/application/saml/test-app/sso/binding/redirect/?SAMLRequest=request";

const mounted: HTMLElement[] = [];

let navigate: ReturnType<typeof vi.spyOn>;

function createStage(challenge: RedirectChallenge): RedirectStage {
    const stage = document.createElement("ak-stage-redirect");

    stage.challenge = challenge;

    document.body.append(stage);
    mounted.push(stage);

    return stage;
}

beforeEach(() => {
    injectBrand({
        flags: {
            flowsContinuousLogin: true,
        },
    });

    navigate = vi.spyOn(RedirectStage.prototype, "navigate").mockImplementation(() => {});
});

afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

describe("RedirectStage", () => {
    it("redirects after a completed flow when resuming other tabs fails", async () => {
        vi.spyOn(Broadcast.prototype, "discoverTabs").mockRejectedValue(
            new Error("Broadcast failed"),
        );

        createStage({ component: "xak-flow-redirect", to: resumeURL, finalRedirect: true });

        await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith(resumeURL));
    });

    it("redirects out of authentik when notifying other tabs of the exit fails", async () => {
        const acsURL = "https://sp.example.com/acs?SAMLResponse=response";

        vi.spyOn(Broadcast.prototype, "discoverTabs").mockResolvedValue(new Set());

        vi.spyOn(Broadcast.prototype, "dispatchExit").mockImplementation(() => {
            throw new DOMException("Access is denied for this document.", "SecurityError");
        });

        createStage({ component: "xak-flow-redirect", to: acsURL, finalRedirect: true });

        await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith(acsURL));
    });

    it("redirects without resuming other tabs when continuous login is disabled", async () => {
        injectBrand({ flags: { flowsContinuousLogin: false } });

        const discoverTabs = vi.spyOn(Broadcast.prototype, "discoverTabs");

        createStage({ component: "xak-flow-redirect", to: resumeURL, finalRedirect: true });

        await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith(resumeURL));

        expect(discoverTabs).not.toHaveBeenCalled();
    });

    it("redirects intermediate hops without resuming other tabs", async () => {
        const discoverTabs = vi.spyOn(Broadcast.prototype, "discoverTabs");

        createStage({ component: "xak-flow-redirect", to: "/source/oauth/login/test-source/" });

        await vi.waitFor(() =>
            expect(navigate).toHaveBeenCalledWith("/source/oauth/login/test-source/"),
        );

        expect(discoverTabs).not.toHaveBeenCalled();
    });
});
