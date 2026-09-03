import "./LDAPSourceStatus.js";

import { LDAPSourceStatus } from "./LDAPSourceStatus.js";

import { LDAPSourceSync, SyncStatusEnum } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

type Connectivity = LDAPSourceStatus["connectivity"];

const minutesAgo = (minutes: number) => new Date(Date.now() - minutes * 60 * 1000);

function makeSync(sync: Partial<LDAPSourceSync> = {}): LDAPSourceSync {
    return {
        pk: "e9f2c1a4-0c9c-4b1a-9a3a-5f7c1f0d2b88",
        tasks: ["c0ffee00-0000-4000-8000-000000000001"],
        source: "1b3a0d9e-1d7a-4c1e-9a1e-3c5d7f9b2a10",
        startedAt: minutesAgo(12),
        finishedAt: minutesAgo(9),
        status: SyncStatusEnum.Done,
        usersCount: 1_204,
        groupsCount: 87,
        membershipCount: 3_311,
        groupHierarchyCount: 42,
        userDeletionsCount: 3,
        groupDeletionsCount: 0,
        ...sync,
    };
}

const CONNECTED: Connectivity = {
    "dc01.foo.example.com": {
        status: "ok",
        vendor: "389 Project",
        version: "389-Directory/2.4.5 B2024.130.1546",
    },
    "dc02.foo.example.com": {
        status: "ok",
        vendor: "389 Project",
        version: "389-Directory/2.4.5 B2024.130.1546",
    },
    "__all__": {
        status: "ok",
        vendor: "389 Project",
        version: "389-Directory/2.4.5 B2024.130.1546",
    },
};

const PARTIAL_OUTAGE: Connectivity = {
    "dc01.foo.example.com": {
        status: "ok",
        vendor: "Microsquish",
        version: "Active Directory 10.0.20348",
    },
    "dc02.foo.example.com": {
        status: "socket connection error while opening: [Errno 111] Connection refused",
    },
    "__all__": {
        status: "ok",
        vendor: "Microsquish",
        version: "Active Directory 10.0.20348",
    },
};

const TOTAL_OUTAGE: Connectivity = {
    "dc01.foo.example.com": {
        status:
            "automatic bind not successful - invalidCredentials - 80090308: " +
            "LdapErr: DSID-0C090447, comment: AcceptSecurityContext error, data 52e, v4563",
    },
    "dc02.foo.example.com": {
        status: "socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)",
    },
    "__all__": {
        status: "no active server available in server pool after maximum number of tries",
    },
};

const NO_SERVER_INFO: Connectivity = {
    "ldap.example.com": { status: "ok", vendor: "N/A", version: "N/A" },
    "__all__": { status: "ok", vendor: "N/A", version: "N/A" },
};

interface StoryArgs {
    connectivity: Connectivity;
    lastSync?: LDAPSourceSync;
}

const metadata: Meta<StoryArgs> = {
    title: "Admin/Sources/LDAP/<ak-source-ldap-status>",
    component: "ak-source-ldap-status",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# LDAP Source Status
`,
            },
        },
    },
};

export default metadata;

type Story = StoryObj<StoryArgs>;

const Template: Story = {
    render: ({ connectivity, lastSync }) => html`
        <div style="max-width: 40rem; padding: 1rem;">
            <ak-source-ldap-status
                .connectivity=${connectivity}
                .lastSync=${lastSync}
            ></ak-source-ldap-status>
        </div>
    `,
};

export const Connected: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync(),
    },
};

export const OneServerDown: Story = {
    ...Template,
    args: {
        connectivity: PARTIAL_OUTAGE,
        lastSync: makeSync({ status: SyncStatusEnum.Warning }),
    },
};

/* Lots of big text */
export const AllServersDown: Story = {
    ...Template,
    args: {
        connectivity: TOTAL_OUTAGE,
        lastSync: makeSync({
            status: SyncStatusEnum.Error,
            startedAt: minutesAgo(65),
            finishedAt: minutesAgo(64),
        }),
    },
};

export const NoVendorMetadata: Story = {
    ...Template,
    args: {
        connectivity: NO_SERVER_INFO,
        lastSync: makeSync(),
    },
};

export const SingleServer: Story = {
    ...Template,
    args: {
        connectivity: {
            "ldap.example.com": {
                status: "ok",
                vendor: "OpenLDAP",
                version: "OpenLDAP 2.6.7",
            },
            "__all__": { status: "ok", vendor: "OpenLDAP", version: "OpenLDAP 2.6.7" },
        },
        lastSync: makeSync(),
    },
};

export const ConnectivityUnknown: Story = {
    ...Template,
    args: {
        connectivity: null,
        lastSync: makeSync(),
    },
};

export const SyncRunning: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({
            status: SyncStatusEnum.Running,
            startedAt: minutesAgo(2),
            finishedAt: null,
        }),
    },
};

export const SyncWarning: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: SyncStatusEnum.Warning }),
    },
};

export const SyncError: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: SyncStatusEnum.Error }),
    },
};

export const SyncFinishedWithoutTimestamp: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: SyncStatusEnum.Error, finishedAt: null }),
    },
};

export const SyncUnknownStatus: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: SyncStatusEnum.UnknownDefaultOpenApi }),
    },
};

export const NothingKnown: Story = {
    ...Template,
    args: {
        connectivity: null,
        lastSync: undefined,
    },
};
