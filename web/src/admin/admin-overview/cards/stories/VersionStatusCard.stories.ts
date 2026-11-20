import "#admin/admin-overview/cards/VersionStatusCard";
import { UpdateVersionReason, Version } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const meta: Meta<Version> = {
    title: "Admin / Overview / Version Status Card",
    component: "ak-admin-status-version",
};

export default meta;

type Story = StoryObj<Version>;

const Template: Story = {
    render: (version) =>
        html`<ak-admin-status-version
            .getPrimaryValue=${() => Promise.resolve(version)}
        ></ak-admin-status-version>`,
};

const upToDate: Version = {
    versionCurrent: "2026.11.0",
    versionLatest: {
        version: "2026.11.0",
        changelog: "",
        changelogUrl: "",
        reason: UpdateVersionReason.Other,
        valid: true,
    },
    buildHash: "",
    outdated: false,
    outpostOutdated: false,
};

export const UpToDate: Story = { ...Template, args: upToDate };

export const UpdateAvailable: Story = {
    ...Template,
    args: {
        ...upToDate,
        versionLatest: { ...upToDate.versionLatest, version: "2026.11.1" },
        outdated: true,
    },
};

export const OutpostOutdated: Story = { ...Template, args: { ...upToDate, outpostOutdated: true } };

export const LatestUnknown: Story = {
    ...Template,
    args: { ...upToDate, versionLatest: { ...upToDate.versionLatest, valid: false } },
};

export const DevelopmentBuild: Story = {
    ...Template,
    args: { ...upToDate, buildHash: "730dc098a1c4e2f5b9d0a7e6f3c1b8d2e5a4f7c0" },
};
