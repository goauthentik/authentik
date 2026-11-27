// Must load before the notifications controller (circular import).
import "#components/notifications/NotificationDrawer";
import "#elements/messages/MessageContainer";
import { createEventFromWSMessage } from "#common/ws/events";

import { NotificationsContextController } from "#elements/controllers/NotificationsContextController";

import { expect, onTestFinished, test } from "vitest";
import { page } from "vitest/browser";

import { LitElement } from "lit";

class NotificationsHost extends LitElement {
    constructor() {
        super();
        this.addController(new NotificationsContextController(this));
    }
}

customElements.define("ak-test-notifications-host", NotificationsHost);

test("links to a relative address", async () => {
    const host = document.createElement("ak-test-notifications-host");
    host.id = "interface-root";
    const messages = document.createElement("ak-message-container");

    onTestFinished(() => {
        host.remove();
        messages.remove();
    });

    document.body.append(host, messages);

    window.dispatchEvent(
        createEventFromWSMessage(
            JSON.parse(`{
                "message_type": "notification.new",
                "id": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                "data": {
                    "pk": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                    "severity": "notice",
                    "body": "User export generated successfully",
                    "hyperlink": "/files/reports/users.csv",
                    "hyperlink_label": "Download",
                    "created": "2026-01-01T00:00:00Z",
                    "event": {
                        "pk": "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                        "action": "export_ready",
                        "app": "authentik.enterprise.reports",
                        "created": "2026-01-01T00:00:00Z"
                    }
                }
            }`),
        ),
    );

    await expect
        .element(page.getByRole("link", { name: "Download" }))
        .toHaveAttribute("href", "/files/reports/users.csv");
});

test("links to an HTTPS address", async () => {
    const host = document.createElement("ak-test-notifications-host");
    host.id = "interface-root";
    const messages = document.createElement("ak-message-container");

    onTestFinished(() => {
        host.remove();
        messages.remove();
    });

    document.body.append(host, messages);

    window.dispatchEvent(
        createEventFromWSMessage(
            JSON.parse(`{
                "message_type": "notification.new",
                "id": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                "data": {
                    "pk": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                    "severity": "notice",
                    "body": "User export generated successfully",
                    "hyperlink": "https://storage.example.com/reports/users.csv",
                    "hyperlink_label": "Download",
                    "created": "2026-01-01T00:00:00Z",
                    "event": {
                        "pk": "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                        "action": "export_ready",
                        "app": "authentik.enterprise.reports",
                        "created": "2026-01-01T00:00:00Z"
                    }
                }
            }`),
        ),
    );

    await expect
        .element(page.getByRole("link", { name: "Download" }))
        .toHaveAttribute("href", "https://storage.example.com/reports/users.csv");
});

test("shows no link for a non-HTTP address", async () => {
    const host = document.createElement("ak-test-notifications-host");
    host.id = "interface-root";
    const messages = document.createElement("ak-message-container");

    onTestFinished(() => {
        host.remove();
        messages.remove();
    });

    document.body.append(host, messages);

    window.dispatchEvent(
        createEventFromWSMessage(
            JSON.parse(`{
                "message_type": "notification.new",
                "id": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                "data": {
                    "pk": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                    "severity": "notice",
                    "body": "User export generated successfully",
                    "hyperlink": "javascript:void(0)",
                    "hyperlink_label": "Download",
                    "created": "2026-01-01T00:00:00Z",
                    "event": {
                        "pk": "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                        "action": "export_ready",
                        "app": "authentik.enterprise.reports",
                        "created": "2026-01-01T00:00:00Z"
                    }
                }
            }`),
        ),
    );

    await expect.element(page.getByRole("link", { name: "View details..." })).toBeVisible();
    // The toast dismisses itself, so check once while it is shown.
    expect(page.getByRole("link", { name: "Download" }).query()).toBeNull();
});

test("shows no link for a non-HTTP address with a leading space and capitals", async () => {
    const host = document.createElement("ak-test-notifications-host");
    host.id = "interface-root";
    const messages = document.createElement("ak-message-container");

    onTestFinished(() => {
        host.remove();
        messages.remove();
    });

    document.body.append(host, messages);

    window.dispatchEvent(
        createEventFromWSMessage(
            JSON.parse(`{
                "message_type": "notification.new",
                "id": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                "data": {
                    "pk": "2b3e5c5e-8f0a-4c1e-9d4b-7a6f1e2d3c4b",
                    "severity": "notice",
                    "body": "User export generated successfully",
                    "hyperlink": " JavaScript:void(0)",
                    "hyperlink_label": "Download",
                    "created": "2026-01-01T00:00:00Z",
                    "event": {
                        "pk": "6f0d1c1e-2f6b-4d3a-9a57-3c1e8b5d2a10",
                        "action": "export_ready",
                        "app": "authentik.enterprise.reports",
                        "created": "2026-01-01T00:00:00Z"
                    }
                }
            }`),
        ),
    );

    await expect.element(page.getByRole("link", { name: "View details..." })).toBeVisible();
    expect(page.getByRole("link", { name: "Download" }).query()).toBeNull();
});
