import "#flow/stages/identification/IdentificationStage";
import { AKFlowUpdateChallengeRequest } from "#flow/events";
import { writePendingSignIn } from "#flow/sources/plex/storage";
import { StageHost } from "#flow/types";

import {
    FlowDesignationEnum,
    IdentificationChallenge,
    LoginSource,
    PlexAuthenticationChallenge,
} from "@goauthentik/api";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

function plexSource(slug: string, name = "Plex"): LoginSource {
    return {
        name,
        challenge: { component: "ak-source-plex", clientId: `${slug}-client`, slug },
    };
}

function challengeOf(overrides: Partial<IdentificationChallenge> = {}): IdentificationChallenge {
    return {
        component: "ak-stage-identification",
        userFields: ["username", "email"],
        passwordFields: false,
        flowDesignation: FlowDesignationEnum.Authentication,
        primaryAction: "Log in",
        showSourceLabels: false,
        sources: [plexSource("plex")],
        ...overrides,
    };
}

const mounted: HTMLElement[] = [];

let challengeRequests: ReturnType<typeof vi.fn<(event: AKFlowUpdateChallengeRequest) => void>>;

beforeEach(() => {
    sessionStorage.clear();

    challengeRequests = vi.fn<(event: AKFlowUpdateChallengeRequest) => void>();
    document.body.addEventListener(AKFlowUpdateChallengeRequest.eventName, challengeRequests);
});

afterEach(() => {
    document.body.removeEventListener(AKFlowUpdateChallengeRequest.eventName, challengeRequests);
    sessionStorage.clear();

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

async function createStage(challenge: IdentificationChallenge) {
    const stage = document.createElement("ak-stage-identification");

    stage.host = { submit: vi.fn() } as unknown as StageHost;
    stage.challenge = challenge;

    document.body.append(stage);
    mounted.push(stage);

    await stage.updateComplete;

    return stage;
}

const requestedChallenges = () =>
    challengeRequests.mock.calls.map(([event]) => event.challenge as PlexAuthenticationChallenge);

describe("IdentificationStage", () => {
    describe("returning from an external source", () => {
        it("hands a returning Plex sign-in back to its source's stage", async () => {
            // The browser arrives at the flow URL from Plex's forwardUrl. The
            // server still has the flow on identification, because the source
            // button swapped in the Plex stage client-side.
            writePendingSignIn({ slug: "plex", pin: 42 });

            await createStage(challengeOf());

            expect(requestedChallenges()).toHaveLength(1);

            expect(requestedChallenges()[0]).toMatchObject({
                component: "ak-source-plex",
                slug: "plex",
            });
        });

        it("picks the source the sign-in started from when there are several", async () => {
            writePendingSignIn({ slug: "plex-family", pin: 42 });

            await createStage(
                challengeOf({
                    sources: [plexSource("plex"), plexSource("plex-family", "Plex (family)")],
                }),
            );

            expect(requestedChallenges()).toHaveLength(1);
            expect(requestedChallenges()[0].slug).toBe("plex-family");
        });

        it("stays on identification when the pending source is not offered here", async () => {
            writePendingSignIn({ slug: "removed-source", pin: 42 });

            const stage = await createStage(challengeOf());

            expect(challengeRequests).not.toHaveBeenCalled();
            expect(stage.shadowRoot?.querySelector("input")).not.toBeNull();
        });

        it("stays on identification when no sign-in is pending", async () => {
            await createStage(challengeOf());

            expect(challengeRequests).not.toHaveBeenCalled();
        });

        it("ignores a pending entry it cannot read", async () => {
            sessionStorage.setItem("authentik-plex-pin", "42");

            await createStage(challengeOf());

            expect(challengeRequests).not.toHaveBeenCalled();
        });
    });

    describe("sole source", () => {
        it("still redirects to a sole source when there is nothing else to fill in", async () => {
            await createStage(challengeOf({ userFields: [] }));

            expect(requestedChallenges()).toHaveLength(1);
            expect(requestedChallenges()[0].slug).toBe("plex");
        });
    });
});
