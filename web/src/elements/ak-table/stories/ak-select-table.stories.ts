import { Meta, StoryObj } from "@storybook/web-components";
import { slug } from "github-slugger";

import { LitElement, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { TableSortEvent } from "../TableColumn.js";
import "../ak-select-table.js";
import { SelectTable } from "../ak-select-table.js";
import { nutritionDbUSDA } from "./sample_nutrition_db.js";

const metadata: Meta<SelectTable> = {
    title: "Elements / Table / SelectTable",
    component: "ak-select-table",
    parameters: {
        docs: {
            description: {
                component: "Our table with a select field",
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
const content = nutritionDbUSDA.map(({ name, calories, sugar, fiber, protein }) => ({
    key: slug(name),
    content: [name, calories, protein, fiber, sugar].map((a) => html`${a}`),
}));

export const Default: Story = {
    render: () =>
        container(
            html`<ak-select-table .columns=${columns} .content=${content}></ak-select-table>`,
        ),
};

export const MultiSelect: Story = {
    render: () =>
        container(
            html`<ak-select-table
                .columns=${columns}
                .content=${content}
                multiple
            ></ak-select-table>`,
        ),
};

type Ord = Record<string | number, string | number>;

@customElement("ak-select-table-test-sort")
export class SimpleTableSortTest extends LitElement {
    @state()
    order = "name";

    @state()
    sortDown = true;

    @property({ type: Boolean, attribute: true })
    multiple = false;

    columns = columns.map((a) => [a, a.toLowerCase()]);

    get content() {
        const content = [...nutritionDbUSDA];

        // Sort according to the key
        const comparison = this.sortDown
            ? (a: Ord, b: Ord) => (a[this.order] > b[this.order] ? -1 : 1)
            : (a: Ord, b: Ord) => (a[this.order] > b[this.order] ? 1 : -1);
        content.sort(comparison);

        // Return the content, processed to comply with the format expected by a selectable table.
        return content.map(({ name, calories, sugar, fiber, protein }) => ({
            key: slug(name),
            content: [name, calories, protein, fiber, sugar].map((a) => html`${a}`),
        }));
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

        return html`<ak-select-table
            .columns=${this.columns}
            .content=${this.content}
            .order="${direction}${this.order}"
            ?multiple=${this.multiple}
            @tablesort=${onTableSort}
        ></ak-select-table>`;
    }
}

export const TableWithSorting: Story = {
    render: () => container(html`<ak-select-table-test-sort></ak-select-table-test-sort>`),
};

export const MultiselectTableWithSorting: Story = {
    render: () => container(html`<ak-select-table-test-sort multiple></ak-select-table-test-sort>`),
};
