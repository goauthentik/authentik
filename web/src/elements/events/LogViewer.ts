import "#components/ak-status-label";
import "#elements/EmptyState";
import "#elements/timestamp/ak-timestamp";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { formatElapsedTime } from "#common/temporal";

import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { P4Disposition } from "#styles/patternfly/constants";

import { LogEvent, LogLevelEnum } from "@goauthentik/api";

import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

const LogLevelError = P.union(LogLevelEnum.Critical, LogLevelEnum.Error, LogLevelEnum.Exception);

const LogLevelWarning = P.union(LogLevelEnum.Warn, LogLevelEnum.Warning);

const logLevelToStatus = (logLevel: LogLevelEnum) =>
    match(logLevel)
        .with(LogLevelError, () => P4Disposition.Error)
        .with(LogLevelWarning, () => P4Disposition.Warning)
        .otherwise(() => P4Disposition.Info);

@customElement("ak-log-viewer")
export class LogViewer extends StaticTable<LogEvent> {
    public static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    public override expandable = true;

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state><span>${msg("No log messages.")}</span> </ak-empty-state>`,
        );
    }

    protected override renderExpanded(item: LogEvent): SlottedTemplateResult {
        return html`<dl class="pf-c-description-list pf-m-horizontal">
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
        </dl>`;
    }

    protected override renderToolbarContainer(): SlottedTemplateResult {
        return null;
    }

    protected columns: TableColumn[] = [
        [msg("Time")],
        [msg("Level")],
        [msg("Event")],
        [msg("Logger")],
    ];

    protected override rowLabel(item: LogEvent): string {
        return formatElapsedTime(item.timestamp);
    }

    protected override row(item: LogEvent): SlottedTemplateResult[] {
        return [
            html`<ak-timestamp .timestamp=${item.timestamp} refresh></ak-timestamp>`,
            html`<ak-status-label
                type=${logLevelToStatus(item.logLevel)}
                bad-label=${item.logLevel}
            ></ak-status-label>`,
            item.event,
            item.logger,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-log-viewer": LogViewer;
    }
}
