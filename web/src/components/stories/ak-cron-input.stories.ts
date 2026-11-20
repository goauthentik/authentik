/**
 * @file Storybook stories for ak-cron-input
 */

import "../ak-cron-input.js";
import { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

interface CronInputProps {
    value?: string;
}

const meta: Meta<CronInputProps> = {
    title: "Components / Cron Input",
    component: "ak-cron-input",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `A text input for a crontab entry. Shows the schedule using cronstrue in readable text.`,
            },
        },
    },
};

export default meta;

type Story = StoryObj<CronInputProps>;

const describe = (story: string) => ({ docs: { description: { story } } });

const container = (testItem: TemplateResult) =>
    html`<div style="padding: 2rem; background: var(--pf-global--BackgroundColor--100)">
        ${testItem}
    </div>`;

const cronInput = (value: string) =>
    container(
        html`<ak-cron-input
            name="crontab"
            label="Crontab"
            required
            value=${value}
        ></ak-cron-input>`,
    );

export const Default: Story = {
    parameters: describe("A valid entry with its description. Edit it to see the text update."),
    render: () => cronInput("*/5 9-17 * * 1-5"),
};

export const Daily: Story = {
    parameters: describe("Times render in 24 hour format."),
    render: () => cronInput("30 14 * * *"),
};

export const Invalid: Story = {
    parameters: describe("An entry that does not parse shows a failure message."),
    render: () => cronInput("not a cron"),
};
