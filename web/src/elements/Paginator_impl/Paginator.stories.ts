/**
 * @file Storybook stories for the default Paginator component implementation
 */

import "../Paginator";
import { Paginator, PageChangeEvent } from "../Paginator";

import { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

interface PaginatorProps {
    totalItems?: number;
    itemsPerPage?: number;
    page?: number;
    label?: string;
}

const meta: Meta<PaginatorProps> = {
    title: "Elements / Paginator",
    component: "ak-paginator",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `Our pagination component`,
            },
        },
    },
};

export default meta;

type Story = StoryObj<PaginatorProps>;

const describe = (story: string) => ({ docs: { description: { story } } });

const container = (testItem: TemplateResult) =>
    html`<div style="padding: 2rem; background: var(--pf-global--BackgroundColor--200)">
        ${testItem}
        <ul id="events" style="margin-top: 1rem"></ul>
    </div>`;

function record(event: PageChangeEvent) {
    console.log(event);

    const item = document.createElement("li");
    item.textContent = `${PageChangeEvent.eventName}: ${event.page}`;
    document.getElementById("events")?.appendChild(item);
    (event.target as Paginator).page = event.page;
}

// Base Paginator: Simple horizontal paginator (equivalent to <hr>)
export const Default: Story = {
    args: {},
    parameters: describe("Basic paginator"),
    render: (args) =>
        container(
            html`<ak-paginator
                item-count="712"
                items-per-page="20"
                page="5"
                @ak-page-changed=${record}
            ></ak-paginator>`,
        ),
};

export const Compact: Story = {
    args: {},
    parameters: describe("Compact paginator"),
    render: (args) =>
        container(
            html`<ak-paginator
                compact
                item-count="712"
                items-per-page="20"
                page="5"
                @ak-page-changed=${record}
            ></ak-paginator>`,
        ),
};
