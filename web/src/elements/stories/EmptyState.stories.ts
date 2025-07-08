import type { Meta, StoryObj } from "@storybook/web-components";

import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { EmptyState, type IEmptyState } from "../EmptyState.js";
import "../EmptyState.js";

const metadata: Meta<EmptyState> = {
    title: "Elements/<ak-empty-state>",
    component: "ak-empty-state",
    parameters: {
        docs: {
            description: "Our empty state spinner",
        },
    },
    argTypes: {
        icon: { control: "text" },
        loading: { control: "boolean" },
        fullHeight: { control: "boolean" },
        header: { control: "text" },
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
        icon: undefined,
        loading: true,
        fullHeight: false,
        header: undefined,
    },

    render: ({ icon, loading, fullHeight, header }: IEmptyState) =>
        container(
            html` <ak-empty-state
                ?loading=${loading}
                ?fullHeight=${fullHeight}
                icon=${ifDefined(icon)}
                header=${ifDefined(header)}
            >
            </ak-empty-state>`,
        ),
};

export const DefaultAndLoadingDone = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ loading: false } },
};

export const DoneWithAlternativeIcon = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{ loading: false, icon: "fa-space-shuttle", header: "The final frontier" },
    },
};

export const WithBodySlotFilled = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{ loading: false, icon: "fa-space-shuttle", header: "The final frontier" },
    },
    render: ({ icon, loading, fullHeight, header }: IEmptyState) =>
        container(html`
            <ak-empty-state
                ?loading=${loading}
                ?fullHeight=${fullHeight}
                icon=${ifDefined(icon)}
                header=${ifDefined(header)}
            >
                <span slot="body">This is the body content</span>
            </ak-empty-state>
        `),
};

export const WithBodyAndPrimarySlotsFilled = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{ loading: false, icon: "fa-space-shuttle", header: "The final frontier" },
    },
    render: ({ icon, loading, fullHeight, header }: IEmptyState) =>
        container(
            html` <ak-empty-state
                ?loading=${loading}
                ?fullHeight=${fullHeight}
                icon=${ifDefined(icon)}
                header=${ifDefined(header)}
            >
                <span slot="body">This is the body content slot</span>
                <span slot="primary">This is the primary content slot</span>
            </ak-empty-state>`,
        ),
};
