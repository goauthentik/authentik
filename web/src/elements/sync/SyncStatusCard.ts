import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/ak-status-label";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/events/LogViewer";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SyncStatus } from "@goauthentik/api";

@customElement("ak-sync-status-card")
export class SyncStatusCard extends AKElement {
    @state()
    syncState?: SyncStatus;

    @state()
    loading = false;

    @property({ attribute: false })
    fetch!: () => Promise<SyncStatus>;

    @property({ attribute: false })
    triggerSync!: () => Promise<unknown>;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFCard, PFTable];
    }

    firstUpdated() {
        this.loading = true;
        this.fetch().then((status) => {
            this.syncState = status;
            this.loading = false;
        });
    }

    renderSyncStatus(): TemplateResult {
        if (this.loading) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        if (!this.syncState) {
            return html`${msg("No sync status.")}`;
        }
        if (this.syncState.isRunning) {
            return html`${msg("Sync currently running.")}`;
        }
        return html`${msg("No synchronization currently running.")}`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__header">
                <div class="pf-c-card__actions">
                    <button
                        class="pf-c-button pf-m-plain"
                        type="button"
                        @click=${() => {
                            this.fetch();
                        }}
                    >
                        <i class="fa fa-sync"></i>
                    </button>
                </div>
                <div class="pf-c-card__title">${msg("Sync status")}</div>
            </div>
            <div class="pf-c-card__body">${this.renderSyncStatus()}</div>
            <div class="pf-c-card__footer">
                <ak-action-button
                    class="pf-m-secondary"
                    ?disabled=${this.syncState?.isRunning}
                    .apiRequest=${() => {
                        if (this.syncState) {
                            // This is a bit of a UX cheat, we set isRunning to true to disable the button
                            // and change the text even before we hear back from the backend
                            this.syncState = {
                                ...this.syncState,
                                isRunning: true,
                            };
                        }
                        this.triggerSync().then(() => {
                            this.dispatchEvent(
                                new CustomEvent(EVENT_REFRESH, {
                                    bubbles: true,
                                    composed: true,
                                }),
                            );
                            this.firstUpdated();
                        });
                    }}
                >
                    ${this.syncState?.isRunning
                        ? msg("Sync currently running")
                        : msg("Run sync again")}
                </ak-action-button>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sync-status-card": SyncStatusCard;
    }
}
