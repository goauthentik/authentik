import { DEFAULT_CONFIG } from "#common/api/config";

import { AdminStatus, AdminStatusCard } from "#admin/admin-overview/cards/AdminStatusCard";
import Styles from "#admin/admin-overview/cards/VersionStatusCard.css";

import { AdminApi, Version } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-admin-status-version")
export class VersionStatusCard extends AdminStatusCard<Version> {
    public static styles = [...super.styles, Styles];

    public override icon = "pf-icon pf-icon-bundle";
    public override label = msg("Version");

    getPrimaryValue(): Promise<Version> {
        return new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve();
    }

    getStatus(value: Version): Promise<AdminStatus> {
        if (value.buildHash) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success",
                message: html`${msg(str`Based on ${value.versionCurrent}`)}`,
            });
        }
        if (value.outdated) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg(str`${value.versionLatest} is available!`)}`,
            });
        }
        if (value.outpostOutdated) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg("An outpost is on an incorrect version!")}
                    <a href="#/outpost/outposts">${msg("Check outposts.")}</a>`,
            });
        }
        if (value.versionLatestValid) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success",
                message: html`${msg("Up-to-date!")}`,
            });
        }
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-question-circle",
            message: html`${msg("Latest version unknown")}`,
        });
    }

    renderValue(): TemplateResult {
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
