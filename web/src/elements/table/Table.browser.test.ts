import { createPaginatedResponse, type PaginatedResponse } from "#common/api/responses";

import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { afterEach, describe, expect, it, vi } from "vitest";

import { html } from "lit";

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

/**
 * A table whose requests resolve only when the test says so, recording the search each was sent
 * with.
 */
class ControlledTable extends StaticTable<Row> {
    public requests: { search: string | undefined; resolve: () => void }[] = [];

    protected override searchEnabled = true;

    protected override columns: TableColumn[] = [["Name"]];

    protected override row(item: Row): SlottedTemplateResult[] {
        return [item.name];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return html`<button>New Row</button>`;
    }

    protected override async apiEndpoint(): Promise<PaginatedResponse<Row, object>> {
        const { search } = this;

        const response = createPaginatedResponse(
            this.items.filter((item) => !search || item.name.includes(search)),
        );

        return new Promise((resolve) => {
            this.requests.push({ search, resolve: () => resolve(response) });
        });
    }
}

customElements.define("ak-test-controlled-table", ControlledTable);

declare global {
    interface HTMLElementTagNameMap {
        "ak-test-instrumented-table": InstrumentedTable;
        "ak-test-controlled-table": ControlledTable;
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
            expect(offscreenTable.visible, "The remaining table still receives entries").toBe(true),
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

describe("Table fetch ordering", () => {
    function createControlledTable(): ControlledTable {
        const table = document.createElement("ak-test-controlled-table");
        table.items = rows;
        document.body.append(table);

        return table;
    }

    it("does not render the empty state while the first fetch is deferred", async () => {
        const table = document.createElement("ak-test-controlled-table");
        table.items = rows;
        document.body.append(createSpacer(), table);

        await table.updateComplete;
        await settleFrames();

        expect(table.visible, "The table below the fold starts invisible").toBe(false);
        expect(table.requests, "An invisible table defers its fetch").toHaveLength(0);

        expect(
            table.shadowRoot?.querySelector('ak-empty-state [slot="primary"]'),
            "The empty state's create button is not rendered before any data arrives",
        ).toBeNull();
    });

    it("runs a search requested during an in-flight fetch once that fetch settles", async () => {
        const table = createControlledTable();

        await vi.waitFor(() => expect(table.requests).toHaveLength(1));

        // Two searches typed while the first page is still loading collapse into one follow-up.
        table.search = "bar";
        const first = table.fetch();
        table.search = "barney";
        const second = table.fetch();

        expect(table.requests, "Nothing is sent while a request is in flight").toHaveLength(1);

        table.requests[0]!.resolve();

        await vi.waitFor(() => expect(table.requests).toHaveLength(2));

        expect(table.requests[1]!.search, "The follow-up uses the latest search").toBe("barney");

        table.requests[1]!.resolve();
        await Promise.all([first, second]);

        expect(table.data?.results.map((row) => row.name)).toEqual(["barney"]);
        expect(table.requests, "Only one follow-up request is sent").toHaveLength(2);
    });
});
