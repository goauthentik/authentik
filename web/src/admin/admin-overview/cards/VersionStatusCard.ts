import {
    AdminStatus,
    AdminStatusCard,
} from "@goauthentik/admin/admin-overview/cards/AdminStatusCard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { AdminApi, Version } from "@goauthentik/api";

@customElement("ak-admin-status-version")
export class VersionStatusCard extends AdminStatusCard<Version> {
    header = t`Version`;
    headerLink = "https://goauthentik.io/docs/releases";
    icon = "pf-icon pf-icon-bundle";

    getPrimaryValue(): Promise<Version> {
        return new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve();
    }

    getStatus(value: Version): Promise<AdminStatus> {
        if (value.buildHash) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success",
                message: html`
                    ${t`Build hash: `}
                    <a
                        href="https://github.com/goauthentik/authentik/commit/${value.buildHash}"
                        target="_blank"
                    >
                        ${value.buildHash?.substring(0, 7)}
                    </a>
                `,
            });
        }
        if (value.outdated) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${t`${value.versionLatest} is available!`}`,
            });
        }
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
            message: html`${t`Up-to-date!`}`,
        });
    }

    renderValue(): TemplateResult {
        return html`${this.value?.versionCurrent}`;
    }
}
