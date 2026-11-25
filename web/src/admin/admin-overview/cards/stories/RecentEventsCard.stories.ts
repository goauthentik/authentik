import "#admin/admin-overview/cards/RecentEventsCard";
import { PaginatedResponse } from "#elements/table/Table";

import { Event, EventActions } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface RecentEventsCardArgs {
    events: Event[];
}

const meta: Meta<RecentEventsCardArgs> = {
    title: "Admin / Overview / Recent Events Card",
    component: "ak-recent-events",
};

export default meta;

type Story = StoryObj<RecentEventsCardArgs>;

const page = (results: Event[]): PaginatedResponse<Event> => ({
    pagination: {
        next: 0,
        previous: 0,
        count: results.length,
        current: 1,
        totalPages: 1,
        startIndex: results.length ? 1 : 0,
        endIndex: results.length,
    },
    results,
});

const Template: Story = {
    render: ({ events }) =>
        html`<ak-recent-events
            .apiEndpoint=${() => Promise.resolve(page(events))}
        ></ak-recent-events>`,
};

const event = (n: number, action: EventActions, username = "akadmin"): Event => ({
    pk: `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`,
    action,
    app: "authentik.events.signals",
    user: { pk: 1, username, email: `${username}@example.com` },
    clientIp: "192.0.2.10",
    context: {},
    created: new Date(Date.now() - n * 60_000),
});

export const WithEvents: Story = {
    ...Template,
    args: {
        events: [
            event(1, EventActions.Login),
            event(2, EventActions.ModelCreated),
            event(5, EventActions.LoginFailed, "jdoe"),
            event(12, EventActions.Logout),
            event(30, EventActions.Login, "jdoe"),
            event(45, EventActions.ModelCreated),
        ],
    },
};

export const Empty: Story = { ...Template, args: { events: [] } };
