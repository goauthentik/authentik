import "#elements/EmptyState";

import { aki } from "#common/api/client";

import { AKElement } from "#elements/Base";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import { Application, CoreApi, RequestableTarget, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";

interface BrowseRow {
    pbmUuid: string;
    label: string;
    parentLabel?: string;
}

function applicationToRow(app: Application): BrowseRow {
    return { pbmUuid: app.pk, label: app.name };
}

function entitlementToRow(target: RequestableTarget): BrowseRow {
    return {
        pbmUuid: target.pbmUuid,
        label: target.label,
        parentLabel: target.parent?.name,
    };
}

@customElement("ak-browse-requestable")
export class BrowseRequestable extends AKElement {
    static styles: CSSResult[] = [PFButton, PFCard, PFCheck, PFContent, PFList, PFStack];

    #coreApi = aki(CoreApi);
    #requestsApi = aki(RequestsApi);

    @state()
    protected applications: BrowseRow[] = [];

    @state()
    protected entitlements: BrowseRow[] = [];

    @state()
    protected loading = true;

    @state()
    protected selected: Set<string> = new Set();

    @state()
    protected submitting = false;

    public override async connectedCallback(): Promise<void> {
        super.connectedCallback();
        await this.refresh();
    }

    protected async refresh(): Promise<void> {
        this.loading = true;
        try {
            const [applications, entitlements] = await Promise.all([
                this.#coreApi.coreApplicationsRequestableList({ pageSize: 100 }),
                this.#coreApi.coreApplicationEntitlementsRequestableList({ pageSize: 100 }),
            ]);
            this.applications = applications.results.map(applicationToRow);
            this.entitlements = entitlements.results.map(entitlementToRow);
        } catch (error) {
            showAPIErrorMessage(error);
        } finally {
            this.loading = false;
        }
    }

    #toggle(pbmUuid: string, checked: boolean): void {
        const next = new Set(this.selected);
        if (checked) {
            next.add(pbmUuid);
        } else {
            next.delete(pbmUuid);
        }
        this.selected = next;
    }

    #requestAccess = async (): Promise<void> => {
        this.submitting = true;
        try {
            const { link } = await this.#requestsApi.requestsGrantRequestsCreate({
                grantRequestCreateRequest: { pbms: Array.from(this.selected) },
            });
            window.location.assign(link);
        } catch (error) {
            showAPIErrorMessage(error);
            this.submitting = false;
        }
    };

    protected renderRow(row: BrowseRow): SlottedTemplateResult {
        return html`<li class="pf-c-list__item" key=${row.pbmUuid}>
            <label class="pf-c-check">
                <input
                    class="pf-c-check__input"
                    type="checkbox"
                    ?checked=${this.selected.has(row.pbmUuid)}
                    @change=${(event: InputEvent) => {
                        this.#toggle(row.pbmUuid, (event.target as HTMLInputElement).checked);
                    }}
                />
                <span class="pf-c-check__label">
                    ${row.parentLabel && row.parentLabel !== row.label
                        ? `${row.parentLabel} / ${row.label}`
                        : row.label}
                </span>
            </label>
        </li>`;
    }

    protected renderSection(title: string, rows: BrowseRow[]): SlottedTemplateResult {
        if (rows.length < 1) {
            return nothing;
        }
        return html`<div class="pf-l-stack__item">
            <div class="pf-c-card">
                <div class="pf-c-card__title">${title}</div>
                <div class="pf-c-card__body">
                    <ul class="pf-c-list" role="list">
                        ${rows.map((row) => this.renderRow(row))}
                    </ul>
                </div>
            </div>
        </div>`;
    }

    protected override render(): SlottedTemplateResult {
        if (this.loading) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        if (this.applications.length < 1 && this.entitlements.length < 1) {
            return html`<ak-empty-state icon="pf-icon-catalog"
                ><span>${msg("Nothing available to request.")}</span>
                <div slot="body">
                    ${msg("There's currently nothing you're eligible to request access to.")}
                </div>
            </ak-empty-state>`;
        }
        return html`<div class="pf-l-stack pf-m-gutter">
            ${this.renderSection(msg("Applications"), this.applications)}
            ${this.renderSection(msg("Application entitlements"), this.entitlements)}
            <div class="pf-l-stack__item">
                <button
                    class="pf-c-button pf-m-primary"
                    type="button"
                    ?disabled=${this.selected.size < 1 || this.submitting}
                    @click=${this.#requestAccess}
                >
                    ${msg("Request access")}
                </button>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-browse-requestable": BrowseRequestable;
    }
}
