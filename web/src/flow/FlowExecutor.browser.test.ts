import { FlowExecutor } from "#flow/FlowExecutor";

import { ChallengeTypes, FlowsApi } from "@goauthentik/api";

import { afterEach, expect, it, vi } from "vitest";

const mounted: HTMLElement[] = [];

afterEach(() => {
    document.querySelectorAll("form[data-test-autosubmit]").forEach((form) => form.remove());
    vi.restoreAllMocks();

    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

it("preserves and disables the current stage during autosubmit navigation", async () => {
    vi.spyOn(FlowsApi.prototype, "flowsExecutorSolve").mockResolvedValue({
        component: "ak-stage-autosubmit",
        url: "https://example.com/sso",
        attrs: { SAMLResponse: "response" },
    });

    const formSubmit = vi
        .spyOn(HTMLFormElement.prototype, "submit")
        .mockImplementation(function submit(this: HTMLFormElement) {
            this.dataset.testAutosubmit = "true";
        });

    const executor = new FlowExecutor();

    const currentChallenge = {
        component: "ak-stage-authenticator-validate",
    } as ChallengeTypes;

    executor.flowSlug = "test-flow";
    executor.challenge = currentChallenge;

    await executor.submit({ component: "ak-stage-authenticator-validate" }, { invisible: true });

    expect(formSubmit).toHaveBeenCalledOnce();
    expect(executor.challenge).toBe(currentChallenge);
    expect(executor.inert).toBe(true);
});

it("renders a new stage element for each stage binding", async () => {
    const createChallenge = (stageBinding: string) =>
        ({ component: "ak-stage-dummy", stageBinding }) as ChallengeTypes;

    const firstChallenge = createChallenge("first");

    vi.spyOn(FlowsApi.prototype, "flowsExecutorGet").mockResolvedValue(firstChallenge);

    const executor = new FlowExecutor();
    executor.flowSlug = "test-flow";
    document.body.append(executor);
    mounted.push(executor);

    const findStage = (challenge: ChallengeTypes) =>
        vi.waitFor(() => {
            const stage = executor.shadowRoot?.querySelector("ak-stage-dummy");

            expect(stage?.challenge).toBe(challenge);

            return stage;
        });

    const firstStage = await findStage(firstChallenge);

    // The same stage shown again, such as after a validation error, keeps its element.
    const repeatedChallenge = createChallenge("first");
    executor.challenge = repeatedChallenge;

    expect(await findStage(repeatedChallenge)).toBe(firstStage);

    // The next stage gets a new element, even though it uses the same component.
    const secondChallenge = createChallenge("second");
    executor.challenge = secondChallenge;

    expect(await findStage(secondChallenge)).not.toBe(firstStage);
});
