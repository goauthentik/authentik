import { formatElapsedTime } from "#common/temporal";

import { PFColor } from "#elements/Label";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { OutpostHealth } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-outpost-health-list")
export class OutpostHealthList extends Table<OutpostHealth> {
    @property({ attribute: false })
    public health: OutpostHealth[] = [];

    async apiEndpoint(): Promise<PaginatedResponse<OutpostHealth>> {
        const items = this.health || [];
        return {
            pagination: {
                count: items.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: items.length,
                next: 0,
                previous: 0,
            },
            results: items,
        };
    }

    protected columns: TableColumn[] = [[msg("Hostname")], [msg("Version")], [msg("Last seen")]];

    protected row(item: OutpostHealth): SlottedTemplateResult[] {
        let versionString = item.version;
        if (item.buildHash) {
            versionString = msg(str`${versionString} (build ${item.buildHash.substring(0, 8)})`);
        }
        if (item.fipsEnabled) {
            versionString = msg(str`${versionString} (FIPS)`);
        }
        return [
            html`${item.hostname}`,
            html`${item.versionOutdated
                ? html`<ak-label color=${PFColor.Red} compact
                      >${msg(str`${item.version}, should be ${item.versionShould}`)}
                  </ak-label>`
                : html`<ak-label color=${PFColor.Green} compact>${versionString} </ak-label>`}`,
            html`<ak-label color=${PFColor.Green} compact>
                ${msg(
                    str`${formatElapsedTime(item.lastSeen)} (${item.lastSeen?.toLocaleTimeString()})`,
                )}
            </ak-label>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-outpost-health-list": OutpostHealthList;
    }
}
