import { submitAutosubmitChallenge } from "#flow/utils/autosubmit";

import { afterEach, expect, it, vi } from "vitest";

afterEach(() => {
    document.querySelectorAll("form[data-test-autosubmit]").forEach((form) => form.remove());
    vi.restoreAllMocks();
});

it("submits an autosubmit challenge using a native form", () => {
    const submit = vi.spyOn(HTMLFormElement.prototype, "submit").mockImplementation(function submit(
        this: HTMLFormElement,
    ) {
        this.dataset.testAutosubmit = "true";
    });

    submitAutosubmitChallenge({
        component: "ak-stage-autosubmit",
        url: "https://example.com/sso",
        attrs: { RelayState: "state", SAMLResponse: "response", submit: "value" },
    });

    const submittedForm = submit.mock.instances[0] as unknown as HTMLFormElement;
    expect(submittedForm.action).toBe("https://example.com/sso");
    expect(submittedForm.method).toBe("post");
    expect(Object.fromEntries(new FormData(submittedForm))).toEqual({
        RelayState: "state",
        SAMLResponse: "response",
        submit: "value",
    });
});
