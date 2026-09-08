import "#elements/forms/DeleteBulkForm";

import { aki } from "#common/api/client";

import { WithLocale } from "#elements/mixins/locale";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { AuthenticatedSession, AuthenticatedSessionGeoIp, CoreApi } from "@goauthentik/api";

import getUnicodeFlagIcon from "country-flag-icons/unicode";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-session-list")
export class AuthenticatedSessionList extends WithLocale(Table<AuthenticatedSession>) {
    public static override verboseName = msg("Session");
    public static override verboseNamePlural = msg("Sessions");

    @property()
    targetUser!: string;

    async apiEndpoint(): Promise<PaginatedResponse<AuthenticatedSession>> {
        return aki(CoreApi).coreAuthenticatedSessionsList({
            ...(await this.defaultEndpointConfig()),
            userUsername: this.targetUser,
        });
    }

    checkbox = true;
    clearOnRefresh = true;
    order = "-expires";

    protected override rowLabel(item: AuthenticatedSession): string | null {
        return item.lastIp ?? null;
    }

    protected formatLocation(geoIp?: AuthenticatedSessionGeoIp | null): string | null {
        if (!geoIp) return null;

        let country: string | null = geoIp.country;

        if (country) {
            try {
                country =
                    new Intl.DisplayNames(this.activeLanguageTag, { type: "region" }).of(country) ??
                    country;
            } catch {
                // Not a region code the runtime knows about, fall back to the raw value.
            }
        }

        const parts = [geoIp.city, country].filter(Boolean);

        return parts.length ? parts.join(", ") : null;
    }

    protected columns: TableColumn[] = [
        [msg("Last IP"), "last_ip"],
        [msg("Last used"), "last_used"],
        [msg("Expires"), "expires"],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Session(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: AuthenticatedSession) => {
                return [
                    { key: msg("Last IP"), value: item.lastIp },
                    { key: msg("Expiry"), value: item.expires?.toLocaleString() || msg("-") },
                ];
            }}
            .usedBy=${(item: AuthenticatedSession) => {
                return aki(CoreApi).coreAuthenticatedSessionsUsedByList({
                    uuid: item.uuid || "",
                });
            }}
            .delete=${(item: AuthenticatedSession) => {
                return aki(CoreApi).coreAuthenticatedSessionsDestroy({
                    uuid: item.uuid || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: AuthenticatedSession): SlottedTemplateResult[] {
        const location = this.formatLocation(item.geoIp);
        const device = [item.userAgent.userAgent?.family, item.userAgent.os?.family]
            .filter(Boolean)
            .join(", ");

        return [
            html`<div>
                    ${item.geoIp?.country
                        ? html`${getUnicodeFlagIcon(item.geoIp.country)}&nbsp;`
                        : nothing}
                    ${item.current ? html`${msg("(Current session)")}&nbsp;` : nothing}
                    ${item.lastIp}
                </div>
                <small>${[location, device].filter(Boolean).join(" — ")}</small>`,
            Timestamp(item.lastUsed),
            Timestamp(item.expires ?? new Date()),
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-session-list": AuthenticatedSessionList;
    }
}
