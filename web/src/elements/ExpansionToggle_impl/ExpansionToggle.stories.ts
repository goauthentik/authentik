/**
 * @file Storybook stories for the default ExpansionToggle component implementation
 */

import "../ExpansionToggle";

import { akExpansionToggle, type ExpansionToggleProps } from "../ExpansionToggle";

import { Meta, StoryObj } from "@storybook/web-components";

import { html, nothing, TemplateResult } from "lit";

const meta: Meta<ExpansionToggleProps> = {
    title: "Elements/ExpansionToggle",
    component: "ak-expansion-toggle",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
The \`angle-right\` control we use in various expansions for the Sidebar, Table Row,
and other controls, isolated into its own control.
\`\`\`html
<ak-expansion-toggle @toggle=\${(ev) => (open = ev.newState === "open")}>
    <span slot="label">Advanced settings</span>
</ak-expansion-toggle>
\`\`\`

The icon is sized in \`em\`, so the whole control scales with the context's font size.
        `,
            },
        },
    },
    argTypes: {
        expanded: {
            control: "boolean",
            description: "The state of the control.",
            table: { defaultValue: { summary: "false" } },
        },
        reversed: {
            control: "boolean",
            description: "Puts the icon after the label.",
            table: { defaultValue: { summary: "false" } },
        },
        content: {
            control: "text",
            description: "The label. Placed into a slot.",
        },
    },
    args: {
        expanded: false,
        reversed: false,
        content: "",
    },
};

export default meta;

type Story = StoryObj<ExpansionToggleProps>;

const describe = (story: string) => ({ docs: { description: { story } } });

const REPORT_ID = "expansion-toggle-report";

const report = (ev: ToggleEvent) => {
    const pad = document.getElementById(REPORT_ID);
    if (pad) pad.textContent = `newState: ${ev.newState}`;
};

const container = (testItem: TemplateResult) => html`
    <div style="padding: 2rem;">
        ${testItem}
        <p id=${REPORT_ID} style="margin-top: 1em;">Nothing toggled yet.</p>
    </div>
`;

const render = ({ expanded, reversed, content }: ExpansionToggleProps) =>
    container(html`
        <ak-expansion-toggle @toggle=${report} ?expanded=${expanded} ?reversed=${reversed}
            >${content ? html`<span slot="label">${content}</span>` : nothing}</ak-expansion-toggle
        >
    `);

export const Default: Story = {
    parameters: describe("Icon only."),
    render,
};

export const WithALabel: Story = {
    ...Default,
    args: { content: "Advanced settings" },
    parameters: describe(
        "Uses a slotted label.  Responds to the surrounding font-size, and so does the icon",
    ),
};

export const Reversed: Story = {
    ...Default,
    args: { content: "Advanced settings", reversed: true },
    parameters: describe("`reversed` icon at the end, like with the Sidebar"),
};

export const StartOpened: Story = {
    ...Default,
    args: { content: "Advanced settings", expanded: true },
    parameters: describe("`expanded` setting starts with the component open."),
    render,
};

export const Bigger: Story = {
    args: { content: "Advanced settings" },
    parameters: describe(
        "The icon is sized in `em`, so the control tracks the inherited font size.",
    ),
    render: ({ content }) =>
        container(html`
            <ak-expansion-toggle @toggle=${report} style="font-size: 32px"
                ><span slot="label">${content}</span></ak-expansion-toggle
            >
        `),
};

export const HelperFunction: Story = {
    parameters: describe(
        "Using the `akExpansionToggle` helper to build a toggle programmatically.",
    ),
    render: () =>
        container(html`
            ${akExpansionToggle({ content: "Built with the function" })}
            ${akExpansionToggle({ content: "Reversed, expanded", reversed: true, expanded: true })}
        `),
};
