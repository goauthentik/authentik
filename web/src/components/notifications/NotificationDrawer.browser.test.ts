import "#components/notifications/NotificationDrawer";

import { NotificationsContext } from "#elements/mixins/notifications";

import { createPaginatedNotificationListFrom } from "#components/notifications/utils";

import { EventActions, SeverityEnum } from "@goauthentik/api";

import { expect, onTestFinished, test } from "vitest";
import { page } from "vitest/browser";

import { ContextProvider } from "@lit/context";

test("links to a relative address", async () => {
    const host = document.createElement("div");
    const notifications = new ContextProvider(host, { context: NotificationsContext });

    notifications.setValue(
        createPaginatedNotificationListFrom([
            {
                pk: "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                severity: SeverityEnum.Notice,
                body: "User export generated successfully",
                hyperlink: "/files/reports/users.csv",
                hyperlinkLabel: "Download",
                created: new Date("2026-01-01T00:00:00Z"),
                event: {
                    pk: "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                    action: EventActions.ExportReady,
                    app: "authentik.enterprise.reports",
                    created: new Date("2026-01-01T00:00:00Z"),
                },
            },
        ]),
    );

    const element = document.createElement("ak-notification-drawer");
    host.append(element);
    onTestFinished(() => host.remove());

    document.body.append(host);
    await element.updateComplete;

    await expect
        .element(page.getByRole("link", { name: "Download" }))
        .toHaveAttribute("href", "/files/reports/users.csv");
});

test("links to an HTTPS address", async () => {
    const host = document.createElement("div");
    const notifications = new ContextProvider(host, { context: NotificationsContext });

    notifications.setValue(
        createPaginatedNotificationListFrom([
            {
                pk: "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                severity: SeverityEnum.Notice,
                body: "User export generated successfully",
                hyperlink: "https://storage.example.com/reports/users.csv",
                hyperlinkLabel: "Download",
                created: new Date("2026-01-01T00:00:00Z"),
                event: {
                    pk: "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                    action: EventActions.ExportReady,
                    app: "authentik.enterprise.reports",
                    created: new Date("2026-01-01T00:00:00Z"),
                },
            },
        ]),
    );

    const element = document.createElement("ak-notification-drawer");
    host.append(element);
    onTestFinished(() => host.remove());

    document.body.append(host);
    await element.updateComplete;

    await expect
        .element(page.getByRole("link", { name: "Download" }))
        .toHaveAttribute("href", "https://storage.example.com/reports/users.csv");
});

test("shows no link for a non-HTTP address", async () => {
    const host = document.createElement("div");
    const notifications = new ContextProvider(host, { context: NotificationsContext });

    notifications.setValue(
        createPaginatedNotificationListFrom([
            {
                pk: "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                severity: SeverityEnum.Notice,
                body: "User export generated successfully",
                // eslint-disable-next-line no-script-url
                hyperlink: "javascript:void(0)",
                hyperlinkLabel: "Download",
                created: new Date("2026-01-01T00:00:00Z"),
                event: {
                    pk: "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                    action: EventActions.ExportReady,
                    app: "authentik.enterprise.reports",
                    created: new Date("2026-01-01T00:00:00Z"),
                },
            },
        ]),
    );

    const element = document.createElement("ak-notification-drawer");
    host.append(element);
    onTestFinished(() => host.remove());

    document.body.append(host);
    await element.updateComplete;

    await expect.element(page.getByText("User export generated successfully")).toBeVisible();
    expect(page.getByRole("link", { name: "Download" }).query()).toBeNull();
});

test("shows no link for a non-HTTP address with a leading space and capitals", async () => {
    const host = document.createElement("div");
    const notifications = new ContextProvider(host, { context: NotificationsContext });

    notifications.setValue(
        createPaginatedNotificationListFrom([
            {
                pk: "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                severity: SeverityEnum.Notice,
                body: "User export generated successfully",
                hyperlink: " JavaScript:void(0)",
                hyperlinkLabel: "Download",
                created: new Date("2026-01-01T00:00:00Z"),
                event: {
                    pk: "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                    action: EventActions.ExportReady,
                    app: "authentik.enterprise.reports",
                    created: new Date("2026-01-01T00:00:00Z"),
                },
            },
        ]),
    );

    const element = document.createElement("ak-notification-drawer");
    host.append(element);
    onTestFinished(() => host.remove());

    document.body.append(host);
    await element.updateComplete;

    await expect.element(page.getByText("User export generated successfully")).toBeVisible();
    expect(page.getByRole("link", { name: "Download" }).query()).toBeNull();
});
