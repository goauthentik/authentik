/**
 * @file Storybook stories for the default Crontab component implementation
 */

import "../Crontab";
import { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

interface CrontabProps {
    cron?: string;
    hideCrontab?: boolean;
}

const meta: Meta<CrontabProps> = {
    title: "Elements / Crontab",
    component: "ak-crontab",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `Displays a crontab entry alongside a human-readable description of the schedule. A string that cannot be parsed shows a fallback message in place of the description.`,
            },
        },
    },
};

export default meta;

type Story = StoryObj<CrontabProps>;

const describe = (story: string) => ({ docs: { description: { story } } });

const container = (testItem: TemplateResult) =>
    html`<div style="padding: 2rem; background: var(--pf-global--BackgroundColor--100)">
        ${testItem}
    </div>`;

export const Default: Story = {
    parameters: describe("A crontab entry with its description."),
    render: () => container(html`<ak-crontab cron="*/5 9-17 * * 1-5"></ak-crontab>`),
};

export const Daily: Story = {
    parameters: describe("Times render in 24 hour format."),
    render: () => container(html`<ak-crontab cron="30 14 * * *"></ak-crontab>`),
};

export const HideCrontab: Story = {
    parameters: describe("`hide-crontab` shows only the description."),
    render: () => container(html`<ak-crontab hide-crontab cron="0 9 * * 1-5"></ak-crontab>`),
};

export const DefaultCron: Story = {
    parameters: describe("With no `cron` attribute the component shows `* * * * *`."),
    render: () => container(html`<ak-crontab></ak-crontab>`),
};

export const Invalid: Story = {
    parameters: describe(
        "An unparseable string keeps the original text and replaces the description.",
    ),
    render: () => container(html`<ak-crontab cron="every tuesday"></ak-crontab>`),
};

export const InAList: Story = {
    parameters: describe("Several entries stacked, as in a schedule table."),
    render: () =>
        container(
            html`<ul style="display: grid; gap: 1rem; list-style: none; padding: 0">
                ${["0 0 * * *", "*/15 * * * *", "0 6 1 * *", "30 2 * * 0"].map(
                    (cron) => html`<li><ak-crontab cron=${cron}></ak-crontab></li>`,
                )}
            </ul>`,
        ),
};

export const Themed: Story = {
    parameters: describe("The custom properties in `Crontab.root.css` restyle every instance."),
    render: () =>
        container(
            html`<ak-crontab
                style="
                    --ak-crontab--Direction: row;
                    --ak-crontab--Gap: var(--pf-global--spacing--lg);
                    --ak-crontab--crontab--Color: var(--pf-global--primary-color--100);
                    --ak-crontab--natural--FontStyle: normal;
                "
                cron="0 9 * * 1-5"
            ></ak-crontab>`,
        ),
};
