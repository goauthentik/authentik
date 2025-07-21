import "../Divider.js";

import { Divider } from "../Divider.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const metadata: Meta<Divider> = {
    title: "Elements/<ak-divider>",
    component: "ak-divider",
    parameters: {
        docs: {
            description: "our most simple divider",
        },
    },
};

export default metadata;

const container = (content: TemplateResult) => html`
    <style>
        ak-divider {
            display: inline-block;
            width: 32rem;
            max-width: 32rem;
        }</style
    >${content}
`;

export const DefaultStory: StoryObj = {
    render: () => container(html` <ak-divider> </ak-divider> `),
};

export const DividerWithSlottedContent: StoryObj = {
    render: () => container(html` <ak-divider><p>Time for bed!</p></ak-divider> `),
};

export const DividerWithSlottedIcon: StoryObj = {
    render: () => container(html` <ak-divider><i class="fa fa-bed"></i></ak-divider> `),
};
