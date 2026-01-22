import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showMessage } from "#elements/messages/MessageContainer";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

type UserMetadata = { key: string; value: string }[];

@customElement("ak-user-bulk-revoke-sessions-table")
export class UserBulkRevokeSessionsTable extends Table<User> {
    paginated = false;

    @property({ attribute: false })
    objects: User[] = [];

    @property({ attribute: false })
    metadata!: (item: User) => UserMetadata;

    @state()
    sessionCounts: Map<number, number> = new Map();

    async apiEndpoint(): Promise<PaginatedResponse<User>> {
        // Fetch session counts for each user
        for (const user of this.objects) {
            try {
                const sessions = await new CoreApi(DEFAULT_CONFIG).coreAuthenticatedSessionsList({
                    userUsername: user.username,
                });
                this.sessionCounts.set(user.pk, sessions.pagination.count);
            } catch {
                this.sessionCounts.set(user.pk, 0);
            }
        }
        this.requestUpdate();

        return Promise.resolve({
            pagination: {
                count: this.objects.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: this.objects.length,
                next: 0,
                previous: 0,
            },
            results: this.objects,
        });
    }

    protected override rowLabel(item: User): string | null {
        return item.username || null;
    }

    protected get columns(): TableColumn[] {
        return [[msg("Username")], [msg("Name")], [msg("Active Sessions")]];
    }

    row(item: User): SlottedTemplateResult[] {
        const sessionCount = this.sessionCounts.get(item.pk);
        return [
            html`${item.username}`,
            html`${item.name || msg("No name set")}`,
            html`${sessionCount !== undefined
                ? sessionCount
                : html`<ak-spinner size="sm"></ak-spinner>`}`,
        ];
    }

    renderToolbarContainer(): SlottedTemplateResult {
        return nothing;
    }
}

@customElement("ak-user-bulk-revoke-sessions")
export class UserBulkRevokeSessionsForm extends ModalButton {
    @property({ attribute: false })
    users: User[] = [];

    @state()
    isRevoking = false;

    @state()
    revokedCount = 0;

    async confirm(): Promise<void> {
        this.isRevoking = true;
        this.revokedCount = 0;

        try {
            // Get user IDs
            const userIds = this.users
                .map((user) => user.pk)
                .filter((pk): pk is number => pk !== undefined);

            // Delete all sessions for these users in a single API call
            if (userIds.length > 0) {
                const response = await new CoreApi(
                    DEFAULT_CONFIG,
                ).coreAuthenticatedSessionsBulkDelete({
                    userPks: userIds,
                });
                this.revokedCount = response.deleted || 0;
            }

            this.onSuccess();
            this.dispatchEvent(
                new CustomEvent(EVENT_REFRESH, {
                    bubbles: true,
                    composed: true,
                }),
            );
            this.open = false;
        } catch (e) {
            this.onError(e as Error);
            throw e;
        } finally {
            this.isRevoking = false;
        }
    }

    onSuccess(): void {
        showMessage({
            message: msg(
                str`Successfully revoked ${this.revokedCount} session(s) for ${this.users.length} user(s)`,
            ),
            level: MessageLevel.success,
        });
    }

    onError(e: Error): void {
        showMessage({
            message: msg(str`Failed to revoke sessions: ${e.toString()}`),
            level: MessageLevel.error,
        });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg("Revoke Sessions")}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p class="pf-c-title">
                        ${msg(
                            str`Are you sure you want to revoke all sessions for ${this.users.length} user(s)?`,
                        )}
                    </p>
                    <p>
                        ${msg(
                            "This will force the selected users to re-authenticate on all their devices.",
                        )}
                    </p>
                </form>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <ak-user-bulk-revoke-sessions-table
                    .objects=${this.users}
                    .metadata=${(item: User) => {
                        return [
                            { key: msg("Username"), value: item.username },
                            { key: msg("Name"), value: item.name || "" },
                        ];
                    }}
                >
                </ak-user-bulk-revoke-sessions-table>
            </section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm();
                    }}
                    class="pf-m-warning"
                >
                    ${msg("Revoke Sessions")} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-bulk-revoke-sessions-table": UserBulkRevokeSessionsTable;
        "ak-user-bulk-revoke-sessions": UserBulkRevokeSessionsForm;
    }
}
