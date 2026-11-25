import "#components/ak-event-info";

import { EventActions } from "@goauthentik/api";

import { expect, onTestFinished, test } from "vitest";
import { page } from "vitest/browser";

test("shows the email body in the preview", async () => {
    const element = document.createElement("ak-event-info");
    onTestFinished(() => element.remove());

    element.event = {
        pk: "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
        action: EventActions.EmailSent,
        app: "authentik.stages.email.tasks",
        created: new Date("2026-01-01T00:00:00Z"),
        user: { pk: 1, username: "akadmin" },
        context: {
            message: "Email to user@example.com sent",
            subject: "Welcome",
            from_email: "noreply@example.com",
            to_email: ["user@example.com"],
            body: "<h1>Welcome</h1>",
        },
    };

    document.body.append(element);
    await element.updateComplete;

    await page.getByRole("button", { name: "Show more" }).click();
    const iframe = element.renderRoot.querySelector("iframe")!;

    await page
        .frameLocator(page.elementLocator(iframe))
        .getByRole("heading", { name: "Welcome" })
        .hover();
});

test("keeps the email preview isolated from the page", async () => {
    const element = document.createElement("ak-event-info");
    onTestFinished(() => element.remove());

    element.event = {
        pk: "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
        action: EventActions.EmailSent,
        app: "authentik.stages.email.tasks",
        created: new Date("2026-01-01T00:00:00Z"),
        user: { pk: 1, username: "akadmin" },
        context: {
            message: "Email to user@example.com sent",
            subject: "Welcome",
            from_email: "noreply@example.com",
            to_email: ["user@example.com"],
            body: "<script>parent.document.body.dataset.preview = 'reached';</script>",
        },
    };

    document.body.append(element);
    await element.updateComplete;

    const iframe = element.renderRoot.querySelector("iframe")!;
    await new Promise((resolve) => iframe.addEventListener("load", resolve, { once: true }));

    expect(document.body.dataset.preview).toBeUndefined();
});
