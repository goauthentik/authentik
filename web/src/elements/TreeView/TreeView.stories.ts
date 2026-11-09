import "../ak-tree-view";
import { akTreeView, type TreeViewProps } from "../ak-tree-view";

import type { Meta, StoryObj } from "@storybook/web-components-vite";

const meta = {
    title: "Elements / <ak-tree-view>",
    component: "ak-tree-view",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `
A collapsible, read-only view of a JSON value. Objects and arrays start collapsed and show a short
summary; click a key to expand it. Strings that contain newlines, or that are wider than the
component, are shown as preformatted blocks.
                `,
            },
        },
    },
    argTypes: {
        value: { control: "object" },
        summaryMaxLength: {
            control: { type: "number", min: 1 },
            description: "Longest string shown in a collapsed summary (`summary-maxlength`)",
        },
        summaryMaxCount: {
            control: { type: "number", min: 1 },
            description: "Most entries shown in a collapsed summary (`summary-maxcount`)",
        },
    },
    args: {
        value: {},
        summaryMaxLength: 15,
        summaryMaxCount: 3,
    },
    render: (args) => akTreeView(args),
} satisfies Meta<TreeViewProps>;

export default meta;

type Story = StoryObj<TreeViewProps>;

export const Default: Story = {
    args: {
        value: {
            model: {
                pk: "02c2e030162d4140ab53a63fc84085c9",
                app: "authentik_core",
                name: "Admirable Commercial Razzmatazz RAC App (a2fdd5)",
                model_name: "application",
            },
            http_request: {
                args: {},
                path: "/api/v3/core/applications/",
                method: "POST",
                user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
        },
    },
};

export const Scalars: Story = {
    args: {
        value: {
            string: "a short string",
            number: 42,
            float: 3.14159,
            enabled: true,
            disabled: false,
            nothing: null,
        },
    },
};

export const Arrays: Story = {
    args: {
        value: {
            groups: ["admins", "editors", "viewers", "auditors"],
            bindings: [
                { order: 0, policy: "require-mfa", negate: false },
                { order: 10, policy: "office-hours", negate: true },
            ],
        },
    },
};

export const EmptyContainers: Story = {
    args: {
        value: { attributes: {}, groups: [], nested: { inner: {} } },
    },
};

export const DeeplyNested: Story = {
    args: {
        value: {
            level1: { level2: { level3: { level4: { level5: { leaf: "found it" } } } } },
        },
    },
};

export const MultilineStrings: Story = {
    args: {
        value: {
            exc_type: "LDAPServerPoolExhaustedError",
            exc_value:
                "no random active server available in server pool after maximum number of tries",
            traceback: [
                "Traceback (most recent call last):",
                '  File "dramatiq/worker.py", line 560, in process_message',
                "    res = actor(*message.args, **message.kwargs)",
                '  File "authentik/sources/ldap/tasks.py", line 70, in ldap_sync',
                "    ldap_sync_paginator(task, source, UserLDAPSynchronizer)",
                '  File "ldap3/core/pooling.py", line 143, in find_active_random_server',
                "    raise LDAPServerPoolExhaustedError(",
                "ldap3.core.exceptions.LDAPServerPoolExhaustedError: no random active server",
            ].join("\n"),
        },
    },
};

export const TightSummaries: Story = {
    args: {
        summaryMaxLength: 5,
        summaryMaxCount: 1,
        value: {
            user: { username: "akadmin", email: "admin@example.com", is_active: true },
        },
    },
};

export const RootArray: Story = {
    args: {
        value: [{ id: 1 }, { id: 2 }, { id: 3 }],
    },
};
