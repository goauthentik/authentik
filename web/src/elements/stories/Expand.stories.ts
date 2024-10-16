import type { Meta, StoryObj } from "@storybook/web-components";

import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { Expand, type IExpand } from "../Expand.js";
import "../Expand.js";

const metadata: Meta<Expand> = {
    title: "Elements/<ak-expand>",
    component: "ak-expand",
    parameters: {
        docs: {
            description: "Our accordion component",
        },
    },
    argTypes: {
        expanded: { control: "boolean" },
        textOpen: { control: "text" },
        textClosed: { control: "text" },
    },
};

export default metadata;

const container = (content: TemplateResult) =>
    html` <div style="background-color: #f0f0f0; padding: 1rem;">
        <style>
            ak-divider {
                display: inline-block;
                width: 32rem;
                max-width: 32rem;
            }</style
        >${content}
    </div>`;

export const DefaultStory: StoryObj = {
    args: {
        expanded: false,
        textOpen: undefined,
        textClosed: undefined,
    },

    render: ({ expanded, textOpen, textClosed }: IExpand) =>
        container(
            html` <ak-expand
                ?expanded=${expanded}
                textOpen=${ifDefined(textOpen)}
                textClosed=${ifDefined(textClosed)}
                ><div>
                    <p>Μήτ᾽ ἔμοι μέλι μήτε μέλισσα</p>
                    <p>"Neither the bee nor the honey for me." - Sappho, 600 BC</p>
                </div>
            </ak-expand>`,
        ),
};
export const Expanded = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ expanded: true } },
};
