import "../ak-library-application-empty-list.js";

import {
    type ILibraryPageApplicationEmptyList,
    LibraryPageApplicationEmptyList,
} from "../ak-library-application-empty-list.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const metadata: Meta<ILibraryPageApplicationEmptyList> = {
    title: "Users / <ak-library-application-empty-list>",
    component: "ak-library-application-empty-list",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Application List Empty State Indicator

A custom component for informing the user that they have no applications. If the user is
an administrator (set via an attribute), a link to the "Create a new application" button
will be provided
`,
            },
        },
    },
    argTypes: {
        admin: { control: "boolean" },
    },
};

export default metadata;

type Story = StoryObj<LibraryPageApplicationEmptyList>;

export const OrdinaryUser: Story = {
    args: {
        admin: false,
    },
    render: ({ admin }: ILibraryPageApplicationEmptyList) =>
        html`<div style="padding: 4em">
            <ak-library-application-empty-list ?admin=${admin}></ak-library-application-empty-list>
        </div> `,
};

export const AdminUser: Story = {
    ...OrdinaryUser,
    args: {
        admin: true,
    },
};
