/**
 * @file Storybook stories for the default Label component implementation
 */

import "../Label";

import { akLabel, type LabelProps } from "../Label";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, type TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const COLORS = ["blue", "green", "orange", "red", "purple", "cyan", "gold", "gray"] as const;

const STATUSES = [
    "danger",
    "error",
    "warning",
    "bad",
    "success",
    "good",
    "ok",
    "running",
    "info",
    "neutral",
    "unknown",
] as const;

type LabelStoryProps = LabelProps & { message: string | TemplateResult };

const meta: Meta<LabelStoryProps> = {
    title: "Elements / Label",
    component: "ak-label",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Labels

These little pill-shaped status indicators are usually called "chips" or "badges", but Patternfly calls them Labels.

## Usage

\`\`\`ts
import "#elements/Label";
\`\`\`

You can mix and match icons as slots or names, and the code is written so that you don't need a wrapper, plain text works fine:

\`\`\`html
<ak-label>♬ I am the very model of a cartoon individual! ♬</ak-label>
\`\`\`

There are three ways to add decorations to the label:

- **\`status\`**: a semantic token (\`success\`, \`danger\`, \`warning\`, …) that selects both a
color and a matching icon in one step. Prefer this for conveying state.  Setting \`status\` will
override the \`color\` setting.
- **\`color\`**: one of the palette tokens (\`blue\`, \`green\`, …) when you want the color without
  the semantics of a status. 
- **\`icon\`**: a Font Awesome class (e.g. \`fa-coffee\`) for an arbitrary leading glyph, or slot
  your own markup with \`slot="icon"\`.  

\`compact\` tightens the padding; \`outline\` swaps the solid fill for a bordered treatment.
`,
            },
        },
    },
    argTypes: {
        status: {
            options: [undefined, ...STATUSES],
            control: { type: "select" },
            description: "Semantic state; sets color and icon together.",
        },
        color: {
            options: [undefined, ...COLORS],
            control: { type: "select" },
            description: "Palette color, independent of any status.",
        },
        icon: {
            control: "text",
            description: "Font Awesome class for a leading icon (e.g. `fa-coffee`).",
        },
        compact: { control: "boolean", description: "Tighter padding for dense layouts." },
        outline: { control: "boolean", description: "Bordered rather than filled." },
        message: { control: "text", description: "Label content." },
    },
    args: {
        message: "Eat at Joe's.",
        compact: false,
        outline: false,
    },
};

export default meta;

type Story = StoryObj<LabelStoryProps>;

const describe = (story: string) => ({ docs: { description: { story } } });

const renderLabel = ({ status, color, icon, compact, outline, message }: LabelStoryProps) => html`
    <ak-label
        status=${ifDefined(status)}
        color=${ifDefined(color)}
        icon=${ifDefined(icon)}
        ?compact=${compact}
        ?outline=${outline}
        >${message}</ak-label
    >
`;

// The interactive playground. With neither status nor color set, this is the
// neutral, informational default.
export const Default: Story = {
    parameters: describe(
        "Interactive label. Use the controls to explore status, color, icon, compact and outline.",
    ),
    render: renderLabel,
};

export const StatusCodes: Story = {
    parameters: describe(
        "Every `status` token. Each selects a color and a matching icon in one step. Takes priority over the `color` attribute.  Prefer using this to the `color` attribute.",
    ),
    render: () => html`
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
            ${STATUSES.map((status) => html`<ak-label status=${status}>${status}</ak-label>`)}
        </div>
    `,
};

export const InvalidStatusCode: Story = {
    parameters: describe(
        "Bad status tokens (here set to 'whatever') will cause a warning to the console.",
    ),
    render: () => html`
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
            <ak-label status="whatever">What<em>ever</em></ak-label>
        </div>
    `,
};

export const Colors: Story = {
    parameters: describe(
        "Our colorful alternative, if a `status` doesn't match your needs.  Maybe you'll need that pastel purple someday.",
    ),
    render: () => html`
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
            ${COLORS.map((color) => html`<ak-label color=${color}>${color}</ak-label>`)}
        </div>
    `,
};

export const Compact: Story = {
    args: { compact: true, status: "warning", message: "It is time for coffee." },
    parameters: describe("`compact` reduces the padding for dense layouts such as table cells."),
    render: renderLabel,
};

export const Outline: Story = {
    parameters: describe("`outline` replaces the solid fill with a border in the same color."),
    render: () => html`
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
            ${COLORS.map((color) => html`<ak-label outline color=${color}>${color}</ak-label>`)}
        </div>
    `,
};

export const IconFromProperty: Story = {
    args: { icon: "fa-coffee", message: "Fresh coffee" },
    parameters: describe("An arbitrary Font Awesome glyph supplied through the `icon` property."),
    render: renderLabel,
};

export const IconFromSlot: Story = {
    parameters: describe(
        'Custom icon markup via slot="icon". The leading gap only appears when icon content is present.',
    ),
    render: () => html`
        <ak-label color="purple">
            <svg
                slot="icon"
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
            >
                <path
                    d="M12 2l2.9 6.3 6.9.6-5.2 4.6 1.6 6.8L12 17.8 5.8 20.9l1.6-6.8L2.2 9.5l6.9-.6z"
                />
            </svg>
            Featured
        </ak-label>
    `,
};

export const Overflow: Story = {
    parameters: describe(
        'Long content is truncated with an ellipsis. Constrain the label\'s width (here via `max-width`) and the `[part="text"]` clip.',
    ),
    render: () => html`
        <ak-label status="info" style="max-width: 16rem;">
            This label's text is far too long to fit and will be truncated with an ellipsis.
        </ak-label>
    `,
};

export const HelperFunction: Story = {
    parameters: describe("Building a label programmatically with the `akLabel` helper function."),
    render: () => akLabel({ status: "success" }, html`Built with <code>akLabel()</code>`),
};
