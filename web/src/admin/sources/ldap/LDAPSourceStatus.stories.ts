import "./LDAPSourceStatus.js";

import { LDAPSourceStatus } from "./LDAPSourceStatus.js";

import { LDAPSourceSync, LDAPSourceSyncStatusEnum } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

/**
 * The shape the server sends for `LDAPSource.connectivity`: one entry per server host, plus a
 * synthetic `__all__` entry for the server pool as a whole. Every value is a string; `status` is
 * either the literal `"ok"` or the stringified `LDAPException` that was raised while connecting.
 * `vendor` and `version` are only present when `status` is `"ok"`.
 *
 * @see authentik/sources/ldap/models.py, `LDAPSource.check_connection`
 */
type Connectivity = LDAPSourceStatus["connectivity"];

const minutesAgo = (minutes: number) => new Date(Date.now() - minutes * 60 * 1000);

/**
 * `LDAPSourceSync` has six read-only fields the component never reads (`pk`, `tasks`, `source`, and
 * the various counts). This builder supplies plausible values for them so the fixtures type-check
 * without casts.
 */
function makeSync(sync: Partial<LDAPSourceSync> = {}): LDAPSourceSync {
    return {
        pk: "e9f2c1a4-0c9c-4b1a-9a3a-5f7c1f0d2b88",
        tasks: ["c0ffee00-0000-4000-8000-000000000001"],
        source: "1b3a0d9e-1d7a-4c1e-9a1e-3c5d7f9b2a10",
        startedAt: minutesAgo(12),
        finishedAt: minutesAgo(9),
        status: LDAPSourceSyncStatusEnum.Done,
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
    "dc01.corp.example.com": {
        status: "ok",
        vendor: "389 Project",
        version: "389-Directory/2.4.5 B2024.130.1546",
    },
    "dc02.corp.example.com": {
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
    "dc01.corp.example.com": {
        status: "ok",
        vendor: "Microsoft",
        version: "Active Directory 10.0.20348",
    },
    "dc02.corp.example.com": {
        status: "socket connection error while opening: [Errno 111] Connection refused",
    },
    "__all__": {
        status: "ok",
        vendor: "Microsoft",
        version: "Active Directory 10.0.20348",
    },
};

/**
 * The realistic worst case for layout: `status` carries the full `str(LDAPException)` text, which
 * is unbounded, untranslated, and printed inline next to the host name.
 */
const TOTAL_OUTAGE: Connectivity = {
    "dc01.corp.example.com": {
        status:
            "automatic bind not successful - invalidCredentials - 80090308: " +
            "LdapErr: DSID-0C090447, comment: AcceptSecurityContext error, data 52e, v4563",
    },
    "dc02.corp.example.com": {
        status: "socket ssl wrapping error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)",
    },
    "__all__": {
        status: "no active server available in server pool after maximum number of tries",
    },
};

/**
 * A server that reported no vendor metadata. The Python side fills both fields with the
 * translated string "N/A" rather than omitting them.
 */
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

A two-row description list summarizing an LDAP source: the per-server connection state cached by
the hourly \`ldap_connectivity_check\` task, and the outcome of the most recent sync.

The component is entirely presentational — it makes no API calls — so every story below is driven
by literal fixtures.

## Reading the fixtures

\`connectivity\` is a map of server host to a flat string dictionary. The key \`__all__\` is not a
host; it is the result of connecting through the round-robin server *pool*, and the component
relabels it as **Global status**. A \`status\` of \`"ok"\` is the only value with \`vendor\` and
\`version\` alongside it; anything else is the stringified exception text.

## Things the stories can't show you statically

The vendor/version detail is inside a \`<pf-tooltip>\`, so it only appears on hover or keyboard
focus of an \`ok\` row. Hover **Global status** in the *Connected* story to see it.

\`\`\`html
<ak-source-ldap-status
    .connectivity=\${source.connectivity}
    .lastSync=\${source.lastSync}
></ak-source-ldap-status>
\`\`\`
`,
            },
        },
    },
};

export default metadata;

type Story = StoryObj<StoryArgs>;

/**
 * Both properties are bound with Lit's `.property` syntax rather than Storybook's automatic
 * attribute binding. `connectivity` is declared as a plain `@property()`, so letting Storybook
 * write it as an attribute would hand the component a string instead of an object.
 */
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
        lastSync: makeSync({ status: LDAPSourceSyncStatusEnum.Warning }),
    },
};

/** The layout stress case: long, unwrapped exception text on every row. */
export const AllServersDown: Story = {
    ...Template,
    args: {
        connectivity: TOTAL_OUTAGE,
        lastSync: makeSync({
            status: LDAPSourceSyncStatusEnum.Error,
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

/** A single-host source: no pool entry beyond `__all__`. */
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

/**
 * `connectivity` is `null` until the connectivity-check task has run at least once — a source
 * created less than an hour ago will look like this.
 */
export const ConnectivityUnknown: Story = {
    ...Template,
    args: {
        connectivity: null,
        lastSync: makeSync(),
    },
};

/** A sync in flight. The component shows "Started at" instead of "Finished at". */
export const SyncRunning: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({
            status: LDAPSourceSyncStatusEnum.Running,
            startedAt: minutesAgo(2),
            finishedAt: null,
        }),
    },
};

export const SyncWarning: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: LDAPSourceSyncStatusEnum.Warning }),
    },
};

export const SyncError: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: LDAPSourceSyncStatusEnum.Error }),
    },
};

/**
 * A terminal status with no `finishedAt`. `finishedAt` is nullable in the schema, and
 * `<ak-timestamp>` renders nothing for a null value, leaving a bare "Finished at" label.
 */
export const SyncFinishedWithoutTimestamp: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: LDAPSourceSyncStatusEnum.Error, finishedAt: null }),
    },
};

/**
 * The OpenAPI generator's catch-all member, emitted when the server sends a status this client
 * build doesn't know about. `<ak-task-status>` falls back to a gray "Unknown" chip.
 */
export const SyncUnknownStatus: Story = {
    ...Template,
    args: {
        connectivity: CONNECTED,
        lastSync: makeSync({ status: LDAPSourceSyncStatusEnum.UnknownDefaultOpenApi }),
    },
};

/** A source that has never synced, on a host that has never been reached. */
export const NothingKnown: Story = {
    ...Template,
    args: {
        connectivity: null,
        lastSync: undefined,
    },
};
