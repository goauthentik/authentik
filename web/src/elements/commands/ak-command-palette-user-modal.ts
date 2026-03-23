import "#elements/LoadingOverlay";

import { DEFAULT_CONFIG } from "#common/api/config";
import { isCausedByAbortError } from "#common/errors/network";

import { AKCommandPaletteModal } from "#elements/commands/ak-command-palette-modal";
import { PaletteCommandDefinition, PaletteCommandNamespace } from "#elements/commands/shared";
import { navigate } from "#elements/router/RouterOutlet";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-command-palette-user-modal")
export class AKCommandPaletteUserModal extends AKCommandPaletteModal {
    #api = new CoreApi(DEFAULT_CONFIG);
    protected loadingOverlay = this.ownerDocument.createElement("ak-loading-overlay");

    public override placeholder = msg("Type a username or email address...", {
        id: "command-palette-placeholder-user-search",
        desc: "Placeholder for the user search command in the admin interface",
    });

    @state()
    protected loading = false;

    #abortController: AbortController | null = null;

    /**
     * A helper function to gracefully handle aborted requests.
     *
     * @see {@linkcode isCausedByAbortError} for the underlying implementation.
     */
    protected suppressAbortError = (error: unknown) => {
        if (isCausedByAbortError(error)) {
            this.logger.info(`Aborted: ${error.message}`);

            return;
        }

        throw error;
    };

    public async refreshUsers(): Promise<void> {
        this.loading = true;
        this.#abortController?.abort();

        this.#abortController = new AbortController();

        return this.#api
            .coreUsersList(
                {
                    isActive: true,
                    includeGroups: true,
                    search: this.value,
                },
                {
                    signal: this.#abortController.signal,
                },
            )
            .then((users) => {
                this.commands = new Set();
                const currentValue = this.value;

                const commands = users.results.map((user): PaletteCommandDefinition => {
                    const label = user.email ? `${user.username} (${user.email})` : user.username;

                    return {
                        namespace: PaletteCommandNamespace.Action,
                        keywords: user.groups,
                        label,
                        action: () => navigate(`/identity/users/${user.pk}`),
                        group: msg("Users"),
                    };
                });
                this.setCommands(commands, [], currentValue);
            })
            .catch(this.suppressAbortError)
            .catch((error) => {
                this.logger.error("Failed to fetch users", error);
                this.setCommands([]);
            })
            .finally(() => {
                this.loading = false;
            });
    }

    #refreshTimeout = -1;

    protected override inputListener = () => {
        clearTimeout(this.#refreshTimeout);

        this.#refreshTimeout = window.setTimeout(() => {
            this.refreshUsers().then(() => {
                this.synchronizeFilteredCommands();
            });
        }, 1000);
    };

    protected override resolveSelectedCommandIndex(event: SubmitEvent): number {
        if (this.loading) {
            return -1;
        }

        return super.resolveSelectedCommandIndex(event);
    }

    protected override createFallbackCommand(): PaletteCommandDefinition | null {
        return null;
    }

    protected override renderCommands(): SlottedTemplateResult {
        if (this.loading) {
            return [this.loadingOverlay, super.renderCommands()];
        }

        return super.renderCommands();
    }

    protected override renderEmpty() {
        if (this.loading && !this.filteredCommands) {
            return html`<ak-empty-state part="empty-state" icon="pf-icon-user" loading
                ><span>${msg("Fetching users...")}</span>
            </ak-empty-state>`;
        }

        return html`<ak-empty-state part="empty-state" icon="pf-icon-user"
            ><span>${msg("No matching users")}</span>
            <div slot="body">
                ${msg("No matching users.", {
                    id: "command-palette.no-matching-users",
                })}
            </div>
        </ak-empty-state>`;
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        this.refreshUsers();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-command-palette-user-modal": AKCommandPaletteUserModal;
    }
}
