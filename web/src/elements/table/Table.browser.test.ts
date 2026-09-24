import { type PaginatedResponse } from "#common/api/responses";

import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { afterEach, describe, expect, it, vi } from "vitest";

interface Row {
    pk: string;
    name: string;
}

class InstrumentedTable extends StaticTable<Row> {
    public fetchCount = 0;

    protected override columns: TableColumn[] = [["Name"]];

    protected override row(item: Row): SlottedTemplateResult[] {
        return [item.name];
    }

    protected override apiEndpoint(): Promise<PaginatedResponse<Row, object>> {
        this.fetchCount += 1;

        return super.apiEndpoint();
    }
}

customElements.define("ak-test-instrumented-table", InstrumentedTable);

declare global {
    interface HTMLElementTagNameMap {
        "ak-test-instrumented-table": InstrumentedTable;
    }
}

const rows: Row[] = [
    { pk: "1", name: "fred" },
    { pk: "2", name: "barney" },
    { pk: "3", name: "wilma" },
    { pk: "4", name: "betty" },
];

function createTable(): InstrumentedTable {
    const table = document.createElement("ak-test-instrumented-table");
    table.items = rows;
    return table;
}

/**
 * A block tall enough to push whatever follows it out of the viewport.
 */
function createSpacer(): HTMLDivElement {
    const spacer = document.createElement("div");
    spacer.style.height = "300vh";

    return spacer;
}

/**
 * Intersection entries arrive after a rendering step, so let a few frames pass before asserting
 * that something did *not* happen.
 */
async function settleFrames(count = 5): Promise<void> {
    for (let i = 0; i < count; i++) {
        await new Promise((resolve) => requestAnimationFrame(resolve));
    }
}

afterEach(() => {
    document.body.replaceChildren();
    window.scrollTo(0, 0);
});

describe("Table observation", () => {
    it("keeps observing a table after another table disconnects", async () => {
        const visibleTable = createTable();
        const offscreenTable = createTable();

        document.body.append(visibleTable, createSpacer(), offscreenTable);

        await vi.waitFor(() => expect(visibleTable.visible).toBe(true));
        await settleFrames();

        expect(offscreenTable.visible, "The table below the fold starts invisible").toBe(false);
        expect(offscreenTable.fetchCount, "An invisible table defers its fetch").toBe(0);

        // Every Table shares one IntersectionObserver. Removing one table must
        // stop observation of that table only.
        visibleTable.remove();

        offscreenTable.scrollIntoView();

        await vi.waitFor(() =>
            expect(offscreenTable.visible, "The remaining table still receives entries").toBe(true)
        );

        expect(offscreenTable.fetchCount, "The deferred fetch runs once visible").toBe(1);
    });
});

describe("Table refetching", () => {
    it("does not refetch when a loaded table leaves and then re-enters the viewport", async () => {
        const table = createTable();

        document.body.append(table, createSpacer());

        await vi.waitFor(() => expect(table.data).not.toBeNull());

        expect(table.fetchCount, "The table fetches once on first entry into the viewport").toBe(1);

        window.scrollTo(0, document.body.scrollHeight);
        await vi.waitFor(() => expect(table.visible).toBe(false));

        window.scrollTo(0, 0);
        await vi.waitFor(() => expect(table.visible).toBe(true));

        await table.updateComplete;
        await settleFrames();

        expect(table.fetchCount, "A scroll round trip should not trigger a fetch").toBe(1);
    });
});
