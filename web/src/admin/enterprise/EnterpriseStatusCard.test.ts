import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { msg } from "@lit/localize";
import { html } from "lit";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import "./EnterpriseStatusCard.js";

describe("ak-enterprise-status-card", () => {
    it("should not error when no data is loaded", async () => {
        render(html`<ak-enterprise-status-card></ak-enterprise-status-card>`);

        const status = await $("ak-enterprise-status-card");
        await expect(status).toHaveText(msg("Loading"));
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

        const status = await $("ak-enterprise-status-card").$(
            ">>>.pf-c-description-list__description > .pf-c-description-list__text",
        );
        await expect(status).toExist();
        await expect(status).toHaveText(msg("Unlicensed"));

        const internalUserProgress = await $("ak-enterprise-status-card").$(
            ">>>#internalUsers > .pf-c-progress__bar",
        );
        await expect(internalUserProgress).toExist();
        await expect(internalUserProgress).toHaveAttr("aria-valuenow", "0");
        const externalUserProgress = await $("ak-enterprise-status-card").$(
            ">>>#externalUsers > .pf-c-progress__bar",
        );
        await expect(externalUserProgress).toExist();
        await expect(externalUserProgress).toHaveAttr("aria-valuenow", "0");
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

        const status = await $("ak-enterprise-status-card").$(
            ">>>.pf-c-description-list__description > .pf-c-description-list__text",
        );
        await expect(status).toExist();
        await expect(status).toHaveText(msg("Valid"));

        const internalUserProgress = await $("ak-enterprise-status-card").$(
            ">>>#internalUsers > .pf-c-progress__bar",
        );
        await expect(internalUserProgress).toExist();
        await expect(internalUserProgress).toHaveAttr("aria-valuenow", "100");

        await expect(
            await $("ak-enterprise-status-card").$(">>>#internalUsers"),
        ).toHaveElementClass("pf-m-warning");

        const externalUserProgress = await $("ak-enterprise-status-card").$(
            ">>>#externalUsers > .pf-c-progress__bar",
        );
        await expect(externalUserProgress).toExist();
        await expect(externalUserProgress).toHaveAttr("aria-valuenow", "100");

        await expect(
            await $("ak-enterprise-status-card").$(">>>#internalUsers"),
        ).toHaveElementClass("pf-m-warning");
        await expect(
            await $("ak-enterprise-status-card").$(">>>#externalUsers"),
        ).toHaveElementClass("pf-m-warning");
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

        const status = await $("ak-enterprise-status-card").$(
            ">>>.pf-c-description-list__description > .pf-c-description-list__text",
        );
        await expect(status).toExist();
        await expect(status).toHaveText(msg("Valid"));

        const internalUserProgress = await $("ak-enterprise-status-card").$(
            ">>>#internalUsers > .pf-c-progress__bar",
        );
        await expect(internalUserProgress).toExist();
        await expect(internalUserProgress).toHaveAttr("aria-valuenow", "100");

        await expect(
            await $("ak-enterprise-status-card").$(">>>#internalUsers"),
        ).toHaveElementClass("pf-m-warning");

        const externalUserProgress = await $("ak-enterprise-status-card").$(
            ">>>#externalUsers > .pf-c-progress__bar",
        );
        await expect(externalUserProgress).toExist();
        await expect(externalUserProgress).toHaveAttr("aria-valuenow", "∞");

        await expect(
            await $("ak-enterprise-status-card").$(">>>#internalUsers"),
        ).toHaveElementClass("pf-m-warning");
        await expect(
            await $("ak-enterprise-status-card").$(">>>#externalUsers"),
        ).toHaveElementClass("pf-m-danger");
    });
});
