import "./EnterpriseStatusCard";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface StatusCardArgs {
    forecast?: LicenseForecast;
    summary?: LicenseSummary;
}

const meta: Meta<StatusCardArgs> = {
    title: "Components / Enterprise Status Card",
    component: "ak-enterprise-status-card",
    tags: ["autodocs"],
};

export default meta;

type Story = StoryObj<StatusCardArgs>;

const Template: Story = {
    render: ({ forecast, summary }: StatusCardArgs) =>
        html`<div style="background-color: #f0f0f0; padding: 1rem;">
            <ak-enterprise-status-card
                .forecast=${forecast}
                .summary=${summary}
            ></ak-enterprise-status-card>
        </div>`,
};

export const Valid: Story = {
    ...Template,
    args: {
        forecast: {
            internalUsers: 20,
            externalUsers: 5,
            forecastedInternalUsers: 24,
            forecastedExternalUsers: 6,
        },
        summary: {
            internalUsers: 100,
            externalUsers: 50,
            status: LicenseSummaryStatusEnum.Valid,
            latestValid: new Date("2027-01-01"),
            licenseFlags: [],
        },
    },
};

export const ExpiringSoon: Story = {
    ...Template,
    args: {
        forecast: {
            internalUsers: 85,
            externalUsers: 40,
            forecastedInternalUsers: 95,
            forecastedExternalUsers: 48,
        },
        summary: {
            internalUsers: 100,
            externalUsers: 50,
            status: LicenseSummaryStatusEnum.ExpirySoon,
            latestValid: new Date(new Date().getTime() + 86400 * 1000 * 14),
            licenseFlags: [],
        },
    },
};

export const ExpiringToday: Story = {
    ...Template,
    args: {
        forecast: {
            internalUsers: 85,
            externalUsers: 40,
            forecastedInternalUsers: 95,
            forecastedExternalUsers: 48,
        },
        summary: {
            internalUsers: 100,
            externalUsers: 50,
            status: LicenseSummaryStatusEnum.ExpirySoon,
            latestValid: new Date(new Date().getTime() + 86400 * 1000 * 0.5),
            licenseFlags: [],
        },
    },
};

export const LimitExceeded: Story = {
    ...Template,
    args: {
        forecast: {
            internalUsers: 120,
            externalUsers: 3,
            forecastedInternalUsers: 140,
            forecastedExternalUsers: 5,
        },
        summary: {
            internalUsers: 100,
            externalUsers: 0,
            status: LicenseSummaryStatusEnum.LimitExceededUser,
            latestValid: new Date("2026-01-01"),
            licenseFlags: [],
        },
    },
};

export const Unlicensed: Story = {
    ...Template,
    args: {
        forecast: {
            internalUsers: 12,
            externalUsers: 4,
            forecastedInternalUsers: 15,
            forecastedExternalUsers: 5,
        },
        summary: {
            internalUsers: 0,
            externalUsers: 0,
            status: LicenseSummaryStatusEnum.Unlicensed,
            latestValid: new Date(0),
            licenseFlags: [],
        },
    },
};

export const Loading: Story = {
    ...Template,
    args: {},
};
