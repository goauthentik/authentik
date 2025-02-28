import { getRelativeTime } from "@goauthentik/common/utils.js";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/elements/EmptyState";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { LogEvent, LogLevelEnum } from "@goauthentik/api";

@customElement("ak-log-viewer")
export class LogViewer extends Table<LogEvent> {
    @property({ attribute: false })
    logs?: LogEvent[] = [];

    expandable = true;
    paginated = false;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(): Promise<PaginatedResponse<LogEvent>> {
        return {
            pagination: {
                next: 0,
                previous: 0,
                count: this.logs?.length || 0,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: this.logs?.length || 0,
            },
            results: this.logs || [],
        };
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state header=${msg("No log messages.")}> </ak-empty-state>`,
        );
    }

    renderExpanded(item: LogEvent): TemplateResult {
        return html`<td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <dl class="pf-c-description-list pf-m-horizontal">
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Timestamp")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                ${item.timestamp.toLocaleString()}
                            </div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${msg("Attributes")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                <pre>${JSON.stringify(item.attributes, null, 4)}</pre>
                            </div>
                        </dd>
                    </div>
                </dl>
            </div>
        </td>`;
    }

    renderToolbarContainer(): TemplateResult {
        return html``;
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Time")),
            new TableColumn(msg("Level")),
            new TableColumn(msg("Event")),
            new TableColumn(msg("Logger")),
        ];
    }

    statusForItem(item: LogEvent): string {
        switch (item.logLevel) {
            case LogLevelEnum.Critical:
            case LogLevelEnum.Error:
            case LogLevelEnum.Exception:
                return "error";
            case LogLevelEnum.Warn:
            case LogLevelEnum.Warning:
                return "warning";
            default:
                return "info";
        }
    }

    row(item: LogEvent): TemplateResult[] {
        return [
            html`${getRelativeTime(item.timestamp)}`,
            html`<ak-status-label
                type=${this.statusForItem(item)}
                bad-label=${item.logLevel}
            ></ak-status-label>`,
            html`${item.event}`,
            html`${item.logger}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-log-viewer": LogViewer;
    }
}
