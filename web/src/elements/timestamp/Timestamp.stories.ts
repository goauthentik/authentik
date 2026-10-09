/**
 * @file Storybook stories for the Timestamp component
 */

import "./ak-timestamp";
import { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

const ago = (ms: number) => new Date(Date.now() - ms);
const fromNow = (ms: number) => new Date(Date.now() + ms);

const meta: Meta = {
    title: "Elements / Timestamp",
    component: "ak-timestamp",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `Renders a point in time as a \`<time>\` element, with an optional relative description ("2 hours ago") and an optional local date and time.

\`timestamp\` must be set as a property (\`.timestamp=\${date}\`); it has no attribute. Add \`hide-elapsed\` to suppress the relative description.`,
            },
        },
    },
};

export default meta;

type Story = StoryObj;

const describe = (story: string) => ({ docs: { description: { story } } });

const container = (testItem: TemplateResult) =>
    html`<div style="padding: 2rem; background: var(--pf-global--BackgroundColor--100)">
        ${testItem}
    </div>`;

export const Default: Story = {
    parameters: describe("A timestamp with its relative description."),
    render: () => container(html`<ak-timestamp .timestamp=${ago(2 * HOUR)}></ak-timestamp>`),
};

export const WithLabel: Story = {
    parameters: describe("Slotted content becomes the label, and names the `<time>` element."),
    render: () =>
        container(html`<ak-timestamp .timestamp=${ago(3 * DAY)}>Last login</ak-timestamp>`),
};

export const WithDateTime: Story = {
    parameters: describe("`datetime` adds the full local date and time."),
    render: () =>
        container(html`<ak-timestamp .timestamp=${ago(3 * DAY)} datetime></ak-timestamp>`),
};

export const DateOnly: Story = {
    parameters: describe("`dateonly` trims the `datetime` output to the local date."),
    render: () =>
        container(html`<ak-timestamp .timestamp=${ago(3 * DAY)} datetime dateonly></ak-timestamp>`),
};

export const WithoutElapsed: Story = {
    parameters: describe("`hide-elapsed` leaves only the date."),
    render: () =>
        container(
            html`<ak-timestamp
                .timestamp=${ago(3 * DAY)}
                hide-elapsed
                datetime
                dateonly
            ></ak-timestamp>`,
        ),
};

export const Future: Story = {
    parameters: describe('Timestamps in the future read as "in 3 hours".'),
    render: () => container(html`<ak-timestamp .timestamp=${fromNow(3 * HOUR)}></ak-timestamp>`),
};

export const Refreshing: Story = {
    parameters: describe(
        "`refresh` keeps the elapsed text current while the element is on screen: every second for the first minute, then every minute. Under `prefers-reduced-motion` it updates once a minute throughout.",
    ),
    render: () =>
        container(
            html`<ak-timestamp .timestamp=${ago(10 * 1000)} refresh datetime>Opened</ak-timestamp>`,
        ),
};

export const Empty: Story = {
    parameters: describe("A null timestamp renders a placeholder."),
    render: () => container(html`<ak-timestamp .timestamp=${null}></ak-timestamp>`),
};

export const Themed: Story = {
    parameters: describe(
        "The document-level custom properties in `Timestamp.root.css` restyle every timestamp.",
    ),
    render: () =>
        container(
            html`<ak-timestamp
                style="
                    --ak-timestamp--FontStyle: italic;
                    --ak-timestamp--Color: var(--pf-global--primary-color--100);
                    --ak-timestamp--FontSize: var(--pf-global--FontSize--md);
                "
                .timestamp=${ago(5 * HOUR)}
                datetime
            ></ak-timestamp>`,
        ),
};
