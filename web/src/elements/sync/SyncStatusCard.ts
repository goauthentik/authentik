import "#components/ak-status-label";
import "#elements/EmptyState";
import "#elements/buttons/ActionButton/index";
import "#elements/events/LogViewer";
import "#elements/tasks/TaskStatus";

import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";

import { SyncStatus } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-sync-status-card")
export class SyncStatusCard extends AKElement {
    @state()
    syncState?: SyncStatus;

    @state()
    loading = false;

    @property({ attribute: false })
    fetch!: () => Promise<SyncStatus>;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFCard, PFDescriptionList, PFStack];
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
        return html`
            <dl class="pf-c-description-list">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Current status")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            ${this.syncState?.isRunning
                                ? html`${msg("Sync is currently running.")}`
                                : html`${msg("Sync is not currently running.")}`}
                        </div>
                    </dd>
                </div>
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text"
                            >${msg("Last successful sync")}</span
                        >
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            ${this.syncState?.lastSuccessfulSync
                                ? html`${formatElapsedTime(this.syncState?.lastSuccessfulSync)}`
                                : html`${msg("No successful sync found.")}`}
                        </div>
                    </dd>
                </div>
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Last sync status")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <ak-task-status
                                .status=${this.syncState?.lastSyncStatus}
                            ></ak-task-status>
                        </div>
                    </dd>
                </div>
            </dl>
        `;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__header">
                <div class="pf-c-card__actions">
                    <button
                        class="pf-c-button pf-m-plain"
                        type="button"
                        @click=${() => {
                            this.fetch().then((status) => {
                                this.syncState = status;
                            });
                        }}
                    >
                        <i class="fa fa-sync"></i>
                    </button>
                </div>
                <div class="pf-c-card__title">${msg("Sync status")}</div>
            </div>
            <div class="pf-c-card__body">${this.renderSyncStatus()}</div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sync-status-card": SyncStatusCard;
    }
}
