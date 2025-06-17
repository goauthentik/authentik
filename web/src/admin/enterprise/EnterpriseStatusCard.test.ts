import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { msg } from "@lit/localize";
import { html } from "lit";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import "./EnterpriseStatusCard.js";

describe("ak-enterprise-status-card", () => {
    it("should not error when no data is loaded", async () => {
        render(html`<ak-enterprise-status-card></ak-enterprise-status-card>`);

        const status = $("ak-enterprise-status-card");
        await expect(status).resolves.toHaveText(msg("Loading"));
    });

    it("should render empty when unlicensed", async () => {
        const forecast: LicenseForecast = {
            externalUsers: 123,
            internalUsers: 123,
            forecastedExternalUsers: 123,
            forecastedInternalUsers: 123,
        };
        const summary: LicenseSummary = {
            status: LicenseSummaryStatusEnum.Unlicensed,
            internalUsers: 0,
            externalUsers: 0,
            latestValid: new Date(0),
            licenseFlags: [],
        };
        render(
            html`<ak-enterprise-status-card .forecast=${forecast} .summary=${summary}>
            </ak-enterprise-status-card>`,
        );

        const status = $("ak-enterprise-status-card").$(
            ">>>.pf-c-description-list__description > .pf-c-description-list__text",
        );
        await expect(status).resolves.toExist();
        await expect(status).resolves.toHaveText(msg("Unlicensed"));

        const internalUserProgress = $("ak-enterprise-status-card").$(
            ">>>#internalUsers > .pf-c-progress__bar",
        );
        await expect(internalUserProgress).resolves.toExist();
        await expect(internalUserProgress).resolves.toHaveAttr("aria-valuenow", "0");
        const externalUserProgress = $("ak-enterprise-status-card").$(
            ">>>#externalUsers > .pf-c-progress__bar",
        );
        await expect(externalUserProgress).resolves.toExist();
        await expect(externalUserProgress).resolves.toHaveAttr("aria-valuenow", "0");
    });

    it("should show warnings when full", async () => {
        const forecast: LicenseForecast = {
            externalUsers: 123,
            internalUsers: 123,
            forecastedExternalUsers: 123,
            forecastedInternalUsers: 123,
        };
        const summary: LicenseSummary = {
            status: LicenseSummaryStatusEnum.Valid,
            internalUsers: 123,
            externalUsers: 123,
            latestValid: new Date(),
            licenseFlags: [],
        };
        render(
            html`<ak-enterprise-status-card .forecast=${forecast} .summary=${summary}>
            </ak-enterprise-status-card>`,
        );

        const status = $("ak-enterprise-status-card").$(
            ">>>.pf-c-description-list__description > .pf-c-description-list__text",
        );
        await expect(status).resolves.toExist();
        await expect(status).resolves.toHaveText(msg("Valid"));

        const internalUserProgress = $("ak-enterprise-status-card").$(
            ">>>#internalUsers > .pf-c-progress__bar",
        );
        await expect(internalUserProgress).resolves.toExist();
        await expect(internalUserProgress).resolves.toHaveAttr("aria-valuenow", "100");

        await expect($("ak-enterprise-status-card").$(">>>#internalUsers")).toHaveElementClass(
            "pf-m-warning",
        );

        const externalUserProgress = $("ak-enterprise-status-card").$(
            ">>>#externalUsers > .pf-c-progress__bar",
        );
        await expect(externalUserProgress).resolves.toExist();
        await expect(externalUserProgress).resolves.toHaveAttr("aria-valuenow", "100");

        await expect(
            $("ak-enterprise-status-card").$(">>>#internalUsers"),
        ).resolves.toHaveElementClass("pf-m-warning");

        await expect(
            $("ak-enterprise-status-card").$(">>>#externalUsers"),
        ).resolves.toHaveElementClass("pf-m-warning");
    });

    it("should show infinity when not licensed for a user type", async () => {
        const forecast: LicenseForecast = {
            externalUsers: 123,
            internalUsers: 123,
            forecastedExternalUsers: 123,
            forecastedInternalUsers: 123,
        };
        const summary: LicenseSummary = {
            status: LicenseSummaryStatusEnum.Valid,
            internalUsers: 123,
            externalUsers: 0,
            latestValid: new Date(),
            licenseFlags: [],
        };
        render(
            html`<ak-enterprise-status-card .forecast=${forecast} .summary=${summary}>
            </ak-enterprise-status-card>`,
        );

        const status = $("ak-enterprise-status-card").$(
            ">>>.pf-c-description-list__description > .pf-c-description-list__text",
        );
        await expect(status).resolves.toExist();
        await expect(status).resolves.toHaveText(msg("Valid"));

        const internalUserProgress = $("ak-enterprise-status-card").$(
            ">>>#internalUsers > .pf-c-progress__bar",
        );
        await expect(internalUserProgress).resolves.toExist();
        await expect(internalUserProgress).resolves.toHaveAttr("aria-valuenow", "100");

        await expect($("ak-enterprise-status-card").$(">>>#internalUsers")).toHaveElementClass(
            "pf-m-warning",
        );

        const externalUserProgress = $("ak-enterprise-status-card").$(
            ">>>#externalUsers > .pf-c-progress__bar",
        );
        await expect(externalUserProgress).resolves.toExist();
        await expect(externalUserProgress).resolves.toHaveAttr("aria-valuenow", "∞");

        await expect(
            $("ak-enterprise-status-card").$(">>>#internalUsers"),
        ).resolves.toHaveElementClass("pf-m-warning");
        await expect(
            $("ak-enterprise-status-card").$(">>>#externalUsers"),
        ).resolves.toHaveElementClass("pf-m-danger");
    });
});
