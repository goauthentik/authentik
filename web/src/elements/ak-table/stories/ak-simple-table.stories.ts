import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { LitElement, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { TableSortEvent } from "../TableColumn.js";
import "../ak-simple-table.js";
import { SimpleTable } from "../ak-simple-table.js";
import { KeyBy } from "../types";
import type { TableRow } from "../types";
import { convertContent } from "../utils.js";
import { nutritionDbUSDA } from "./sample_nutrition_db.js";

const metadata: Meta<SimpleTable> = {
    title: "Elements / Table / SimpleTable",
    component: "ak-simple-table",
    parameters: {
        docs: {
            description: {
                component: "Our basic table",
            },
        },
    },
    argTypes: {
        content: {
            type: "function",
            description: "An array of arrays of items to show",
        },
        columns: {
            type: "function",
            description: "An array of column headers",
        },
        order: {
            type: "string",
            description:
                "A key indicating which column to highlight as the current sort target, if any",
        },
    },
};

export default metadata;

type Story = StoryObj;

const container = (testItem: TemplateResult) =>
    html` <div style="background: #fff; padding: 2em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        ${testItem}
    </div>`;

const columns = ["Name", "Calories", "Protein", "Fiber", "Sugar"];
const content = nutritionDbUSDA.map(({ name, calories, sugar, fiber, protein }) => [
    name,
    calories,
    protein,
    fiber,
    sugar,
]);

export const Default: Story = {
    render: () =>
        container(
            html`<ak-simple-table .columns=${columns} .content=${content}></ak-simple-table>`,
        ),
};

type Ord = Record<string | number, string | number>;

@customElement("ak-simple-table-test-sort")
export class SimpleTableSortTest extends LitElement {
    @state()
    order = "name";

    @state()
    sortDown = true;

    columns = columns.map((a) => [a, a.toLowerCase()]);

    get content() {
        const content = [...nutritionDbUSDA];
        const comparison = this.sortDown
            ? (a: Ord, b: Ord) => (a[this.order] < b[this.order] ? -1 : 1)
            : (a: Ord, b: Ord) => (a[this.order] < b[this.order] ? 1 : -1);
        content.sort(comparison);
        return content.map(({ name, calories, sugar, fiber, protein }) => [
            name,
            calories,
            protein,
            fiber,
            sugar,
        ]);
    }

    render() {
        const onTableSort = (event: TableSortEvent) => {
            if (event.value === this.order) {
                this.sortDown = !this.sortDown;
                return;
            }
            this.order = event.value;
        };

        const direction = this.sortDown ? "" : "-";

        return html`<ak-simple-table
            .columns=${this.columns}
            .content=${this.content}
            .order="${direction}${this.order}"
            @tablesort=${onTableSort}
        ></ak-simple-table>`;
    }
}

export const TableWithSorting: Story = {
    render: () => container(html`<ak-simple-table-test-sort></ak-simple-table-test-sort>`),
};

const rowContent: TableRow[] = nutritionDbUSDA.map(({ name, calories, sugar, fiber, protein }) => ({
    key: slug(name),
    content: [name, calories, protein, fiber, sugar].map((a) => html`${a}`),
}));

export const PreprocessedContent: Story = {
    render: () =>
        container(
            html`<ak-simple-table .columns=${columns} .content=${rowContent}></ak-simple-table>`,
        ),
};

const capitalize = (s = "") => `${s.substring(0, 1).toUpperCase()}${s.substring(1)}`;

const groups = new Map(nutritionDbUSDA.map(({ name, group }) => [name, group]));
const groupFoods: KeyBy = (content) => capitalize(groups.get(content[0] as string));
const groupedContent = convertContent(content, { groupBy: groupFoods });

export const GroupedTable: Story = {
    render: () =>
        html`<ak-simple-table .columns=${columns} .content=${groupedContent}></ak-simple-table>`,
};
