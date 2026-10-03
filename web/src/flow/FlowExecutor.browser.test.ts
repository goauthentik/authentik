import { FlowExecutor } from "#flow/FlowExecutor";

import { ChallengeTypes, FlowsApi } from "@goauthentik/api";

import { afterEach, expect, it, vi } from "vitest";

afterEach(() => {
    document.querySelectorAll("form[data-test-autosubmit]").forEach((form) => form.remove());
    vi.restoreAllMocks();
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
