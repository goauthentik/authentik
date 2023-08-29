import {
    AdminStatus,
    AdminStatusCard,
} from "@goauthentik/admin/admin-overview/cards/AdminStatusCard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { AdminApi, Version } from "@goauthentik/api";

@customElement("ak-admin-status-version")
export class VersionStatusCard extends AdminStatusCard<Version> {
    icon = "pf-icon pf-icon-bundle";

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
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
            message: html`${msg("Up-to-date!")}`,
        });
    }

    renderHeader(): TemplateResult {
        return html`${msg("Version")}`;
    }

    renderValue(): TemplateResult {
        let text = this.value?.versionCurrent;
        const versionFamily = this.value?.versionCurrent.split(".");
        versionFamily?.pop();
        let link = `https://goauthentik.io/docs/releases/${versionFamily?.join(".")}`;
        if (this.value?.buildHash) {
            text = this.value.buildHash?.substring(0, 7);
            link = `https://github.com/goauthentik/authentik/commit/${this.value.buildHash}`;
        }
        return html`<a href=${link} target="_blank">${text}</a>`;
    }
}
