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
        // TODO: use WithVersion and maybe expose the promise so this all works correctly.
        return aki(AdminApi).adminVersionRetrieve();
    }

    public async getStatus(value: Version): Promise<AdminStatus> {
        if (import.meta.env.GIT_BUILD_HASH) {
            return {
                icon: "fa fa-check-circle pf-m-success",
                message: msg(str`Based on ${import.meta.env.AK_VERSION}`),
                tone: "success",
            };
        }

        if (!value.versionLatest?.valid) {
            return {
                icon: "fa fa-question-circle",
                message: msg("Latest version unknown"),
                tone: "neutral",
            };
        }

        // TODO: This could only be true if versionLatest.valid is also true.
        // Fix type union.
        if (value.outdated) {
            const upstreamVersion = value.versionLatest?.version;

            const message = upstreamVersion
                ? msg(str`${upstreamVersion} is available!`)
                : msg(str`A new version is available!`);

            return {
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message,
                tone: "warning",
            };
        }

        if (value.outpostOutdated) {
            return {
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg("An outpost is on an incorrect version!")}&nbsp;<a
                        href=${toAdminInterface("outpost/outposts")}
                        >${msg("Check outposts.")}</a
                    >`,
                tone: "warning",
            };
        }

        return {
            icon: "fa fa-check-circle pf-m-success",
            message: msg("Up-to-date!"),
            tone: "success",
        };
    }

    protected renderValue(): SlottedTemplateResult {
        let text = import.meta.env.AK_VERSION;
        let link = import.meta.env.AK_DOCS_RELEASE_NOTES_URL;

        if (import.meta.env.GIT_BUILD_HASH) {
            text = import.meta.env.GIT_BUILD_HASH.substring(0, 7);
            link = `https://github.com/goauthentik/authentik/commit/${import.meta.env.GIT_BUILD_HASH}`;
        }

        return html`<a rel="noopener noreferrer" href=${link} target="_blank">${text}</a>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-version": VersionStatusCard;
    }
}
