import { aki } from "#common/api/client";

import { toAdminInterface } from "#elements/router/core/interfaces";
import { SlottedTemplateResult } from "#elements/types";

import { AdminStatus, AdminStatusCard } from "#admin/admin-overview/cards/AdminStatusCard";
import Styles from "#admin/admin-overview/cards/VersionStatusCard.css";

import { AdminApi, Version } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-admin-status-version")
export class VersionStatusCard extends AdminStatusCard<Version> {
    public static styles = [...super.styles, Styles];

    public override icon = "pf-icon pf-icon-bundle";
    public override label = msg("Version");

    public getPrimaryValue(): Promise<Version> {
        return aki(AdminApi).adminVersionRetrieve();
    }

    public async getStatus(value: Version): Promise<AdminStatus> {
        if (value.buildHash) {
            return {
                icon: "fa fa-check-circle pf-m-success",
                message: msg(str`Based on ${value.versionCurrent}`),
                tone: "success",
            };
        }

        if (value.outdated) {
            return {
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: msg(str`${value.versionLatest?.version} is available!`),
                tone: "warning",
            };
        }

        if (value.outpostOutdated) {
            return {
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message:
                    msg("An outpost is on an incorrect version!") +
                    ` <a href=${toAdminInterface("outpost/outposts")}>${msg("Check outposts.")}</a>`,
                tone: "warning",
            };
        }

        if (value.versionLatest?.valid) {
            return {
                icon: "fa fa-check-circle pf-m-success",
                message: html`${msg("Up-to-date!")}`,
                tone: "success",
            };
        }

        return {
            icon: "fa fa-question-circle",
            message: msg("Latest version unknown"),
            tone: "",
        };
    }

    protected renderValue(): SlottedTemplateResult {
        let text = this.value?.versionCurrent;
        const versionFamily = this.value?.versionCurrent.split(".");
        versionFamily?.pop();
        let link = `https://docs.goauthentik.io/releases/${versionFamily?.join(".")}`;

        if (this.value?.buildHash) {
            text = this.value.buildHash?.substring(0, 7);
            link = `https://github.com/goauthentik/authentik/commit/${this.value.buildHash}`;
        }

        return html`<a rel="noopener noreferrer" href=${link} target="_blank">${text}</a>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-version": VersionStatusCard;
    }
}
