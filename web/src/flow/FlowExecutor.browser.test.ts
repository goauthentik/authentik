import "#elements/messages/MessageContainer";
import { FlowExecutor } from "#flow/FlowExecutor";

import {
    ChallengeTypes,
    ContextualFlowInfoLayoutEnum,
    FlowMessageLevelEnum,
    FlowsApi,
} from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";

const mounted: HTMLElement[] = [];

function emailChallengeOf(...messages: string[]): ChallengeTypes {
    return {
        component: "ak-stage-email",
        flowInfo: {
            cancelUrl: "/flows/-/cancel/",
            layout: ContextualFlowInfoLayoutEnum.Stacked,
            messages: messages.map((message) => ({ level: FlowMessageLevelEnum.Success, message })),
        },
    };
}

async function createExecutor(): Promise<FlowExecutor> {
    const container = document.createElement("ak-message-container");
    const executor = new FlowExecutor();

    vi.spyOn(executor, "refresh").mockResolvedValue(true);

    executor.flowSlug = "test-flow";
    executor.challenge = emailChallengeOf();

    document.body.append(container, executor);
    mounted.push(container, executor);

    await executor.updateComplete;

    return executor;
}

function shownMessages(): string[] {
    return document.querySelector("ak-message-container")!.messages.map(({ message }) => message);
}

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

describe("FlowExecutor messages", () => {
    it("shows the messages of every challenge returned by a submission", async () => {
        vi.spyOn(FlowsApi.prototype, "flowsExecutorSolve").mockImplementation(async () =>
            emailChallengeOf("Email Successfully sent."),
        );

        const executor = await createExecutor();

        await executor.submit({ component: "ak-stage-email" });
        await executor.submit({ component: "ak-stage-email" });
        await executor.updateComplete;

        expect(shownMessages()).toEqual(["Email Successfully sent.", "Email Successfully sent."]);
    });

    it("does not show the messages again when the theme changes", async () => {
        vi.spyOn(FlowsApi.prototype, "flowsExecutorSolve").mockResolvedValue(
            emailChallengeOf("Email Successfully sent."),
        );

        const executor = await createExecutor();

        await executor.submit({ component: "ak-stage-email" });
        await executor.updateComplete;

        executor.activeTheme = executor.activeTheme === "dark" ? "light" : "dark";
        await executor.updateComplete;

        expect(shownMessages()).toEqual(["Email Successfully sent."]);
    });
});
