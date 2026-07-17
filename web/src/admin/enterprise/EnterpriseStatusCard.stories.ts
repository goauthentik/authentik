import "./EnterpriseStatusCard.js";

import {
    LicenseForecast,
    LicenseSummary,
    LicenseSummaryStatusEnum,
} from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface StatusCardArgs {
    forecast?: LicenseForecast;
    summary?: LicenseSummary;
}

const metadata: Meta<StatusCardArgs> = {
    title: "Admin/Enterprise/<ak-enterprise-status-card>",
    component: "ak-enterprise-status-card",
};

export default metadata;

const render = ({ forecast, summary }: StatusCardArgs) =>
    html`<div style="background-color: #f0f0f0; padding: 1rem;">
        <ak-enterprise-status-card
            .forecast=${forecast}
            .summary=${summary}
        ></ak-enterprise-status-card>
    </div>`;

/**
 * A healthy, valid license with usage comfortably within the licensed seat
 * counts — both progress bars render in their default (neutral) color.
 */
export const Valid: StoryObj<StatusCardArgs> = {
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
    render,
};

/**
 * A valid license nearing expiry with internal usage past the 80% mark, which
 * escalates that bar to its warning color.
 */
export const ExpiringSoon: StoryObj<StatusCardArgs> = {
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
            latestValid: new Date("2026-08-01"),
            licenseFlags: [],
        },
    },
    render,
};

/**
 * Usage has exceeded the licensed seat counts. The internal bar goes past 100%
 * (danger), and the external count against zero licensed external seats yields
 * the "∞%" case handled by `calcUserPercentage`.
 */
export const LimitExceeded: StoryObj<StatusCardArgs> = {
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
            status: LicenseSummaryStatusEnum.Expired,
            latestValid: new Date("2026-01-01"),
            licenseFlags: [],
        },
    },
    render,
};

/**
 * No license present. Both usage percentages are forced to 0 regardless of the
 * forecasted counts, and the badge reads "Unlicensed".
 */
export const Unlicensed: StoryObj<StatusCardArgs> = {
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
    render,
};

/**
 * Neither property is supplied, exercising the component's "Loading" fallback.
 */
export const Loading: StoryObj<StatusCardArgs> = {
    args: {},
    render,
};
