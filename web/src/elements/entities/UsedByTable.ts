import { PFSize } from "#common/enums";

import { UsedByListItem } from "#elements/entities/used-by";
import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/TableColumn";
import { SlottedTemplateResult } from "#elements/types";

import { type UsedBy } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues } from "lit";
import { html } from "lit-html";
import { until } from "lit-html/directives/until.js";
import { customElement, property, state } from "lit/decorators.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

export interface BulkDeleteMetadata {
    key: string;
    value: string;
}

@customElement("ak-used-by-table")
export class UsedByTable<T extends object> extends StaticTable<T> {
    static styles: CSSResult[] = [...super.styles, PFList];

    @property({ attribute: false })
    public metadata: (item: T) => BulkDeleteMetadata[] = (item: T) => {
        const metadata: BulkDeleteMetadata[] = [];

        if ("name" in item) {
            metadata.push({ key: msg("Name"), value: item.name as string });
        }
        return metadata;
    };

    @property({ attribute: false })
    public usedBy: null | ((item: T) => Promise<UsedBy[]>) = null;

    @state()
    protected usedByData: Map<T, UsedBy[]> = new Map();

    protected override rowLabel(item: T): string | null {
        const name = "name" in item && typeof item.name === "string" ? item.name.trim() : null;
        return name || null;
    }

    @state()
    protected get columns(): TableColumn[] {
        const [first] = this.items || [];

        if (!first) {
            return [];
        }

        return this.metadata(first).map((element) => [element.key]);
    }

    protected override row(item: T): SlottedTemplateResult[] {
        return this.metadata(item).map((element) => element.value);
    }

    protected override renderToolbarContainer(): SlottedTemplateResult {
        return null;
    }

    protected override firstUpdated(changedProperties: PropertyValues<this>): void {
        this.expandable = !!this.usedBy;

        super.firstUpdated(changedProperties);
    }

    protected override renderExpanded(item: T): SlottedTemplateResult {
        const handler = async () => {
            if (!this.usedByData.has(item) && this.usedBy) {
                this.usedByData.set(item, await this.usedBy(item));
            }
            return this.renderUsedBy(this.usedByData.get(item) || []);
        };
        return html`${this.usedBy
            ? until(handler(), html`<ak-spinner size=${PFSize.Large}></ak-spinner>`)
            : null}`;
    }

    protected renderUsedBy(usedBy: UsedBy[]): SlottedTemplateResult {
        if (usedBy.length < 1) {
            return html`<span>${msg("Not used by any other object.")}</span>`;
        }
        return html`<ul class="pf-c-list">
            ${usedBy.map((ub) => UsedByListItem({ ub }))}
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-used-by-table": UsedByTable<object>;
    }
}
