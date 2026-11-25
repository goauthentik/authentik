import "#admin/policies/PolicyListPage";
import "#elements/Label";
import { PaginatedResponse } from "#elements/table/Table";

import { Policy } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface PolicyListPageArgs {
    policies: Policy[];
}

const meta: Meta<PolicyListPageArgs> = {
    title: "Admin / Policies / Policy List Page",
    component: "ak-policy-list",
};

export default meta;

type Story = StoryObj<PolicyListPageArgs>;

const page = (results: Policy[]): PaginatedResponse<Policy> => ({
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
    render: ({ policies }) =>
        html`<ak-policy-list
            .apiEndpoint=${() => Promise.resolve(page(policies))}
        ></ak-policy-list>`,
};

const policy = (
    n: number,
    name: string,
    kind: string,
    verboseName: string,
    boundTo: number,
): Policy => ({
    pk: `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`,
    name,
    component: `ak-policy-${kind}-form`,
    verboseName,
    verboseNamePlural: `${verboseName}s`,
    metaModelName: `authentik_policies_${kind}.${kind}policy`,
    boundTo,
    lastUpdated: new Date(Date.now() - n * 3_600_000),
    created: new Date(Date.now() - n * 86_400_000),
});

export const WithPolicies: Story = {
    ...Template,
    args: {
        policies: [
            policy(
                1,
                "default-authentication-flow-password-stage",
                "expression",
                "Expression Policy",
                1,
            ),
            policy(2, "default-password-change-password-policy", "password", "Password Policy", 3),
            policy(3, "default-source-enrollment-if-sso", "expression", "Expression Policy", 1),
            policy(4, "brute-force-reputation", "reputation", "Reputation Policy", 12),
            policy(5, "login-failed-matcher", "event_matcher", "Event Matcher Policy", 0),
            policy(6, "quarterly-password-expiry", "expiry", "Password Expiry Policy", 0),
        ],
    },
};

export const Empty: Story = { ...Template, args: { policies: [] } };
