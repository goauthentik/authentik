import "../ak-structured-view";
import { akStructuredView, type StructuredViewProps } from "../ak-structured-view";

import type { Meta, StoryObj } from "@storybook/web-components-vite";

const meta = {
    title: "Elements / <ak-structured-view>",
    component: "ak-structured-view",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `
A "pretty" view of structured JSON data.  Does summary/disclosure of objects in a progressive scheme, so large attribute collection objects can be reviewed without having to face a massive vall of text.  Strings with newlines and strings that won't fit in the horizontal viewport are shown is preformat blocks with overflow.
                `,
            },
        },
    },
    argTypes: {
        value: { control: "object" },
        summaryMaxLength: {
            control: { type: "number", min: 1 },
            description: "Max length of a string shown in a summary (`summary-maxlength`)",
        },
        summaryMaxCount: {
            control: { type: "number", min: 1 },
            description: "Max number of entries shown in a summary (`summary-maxcount`)",
        },
    },
    args: {
        value: {},
        summaryMaxLength: 15,
        summaryMaxCount: 3,
    },
    render: (args) => akStructuredView(args),
} satisfies Meta<StructuredViewProps>;

export default meta;

type Story = StoryObj<StructuredViewProps>;

export const Default: Story = {
    args: {
        value: {
            model: {
                pk: "02c2e030162d4140ab53a63fc84085c9",
                app: "authentik_core",
                name: "Those Meddling Kids RAC App (a2fdd5)",
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
