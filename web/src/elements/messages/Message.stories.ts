/**
 * @file Storybook stories for the Message (toast) element
 */

import "./Message";
import { MessageLevel } from "#common/messages";

import { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";

const meta: Meta = {
    title: "Elements / Message",
    component: "ak-message",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `A toast alert. In the app, \`<ak-message-container>\` renders one message; use \`showMessage()\` from \`#elements/messages/MessageContainer\` to create new messages.

The default slot is the title. \`description\` (string or template) and \`onDismiss\` are properties only. \`onDismiss\` runs when the close button is clicked and, after \`lifetime\` milliseconds (default 8000), from a timer. Without \`onDismiss\` there is no timer. \`live\` implies \`aria-live\`.`,
            },
        },
    },
};

export default meta;

type Story = StoryObj;

const describe = (story: string) => ({ docs: { description: { story } } });

// ak-message renders an <li>, so it belongs in a list
const container = (testItem: TemplateResult) =>
    html`<div style="padding: 2rem; background: var(--pf-global--BackgroundColor--100)">
        <ul style="list-style: none; margin: 0; padding: 0; max-width: 30rem">
            ${testItem}
        </ul>
    </div>`;

const removeById = (id: string) => () => document.getElementById(id)?.remove();

export const Default: Story = {
    parameters: describe("The default level is `info`."),
    render: () => container(html`<ak-message>Changes saved to draft.</ak-message>`),
};

export const Levels: Story = {
    parameters: describe("Each `level` sets the alert colour and its default icon."),
    render: () =>
        container(
            html`${Object.values(MessageLevel).map(
                (level) =>
                    html`<ak-message level=${level}>A message at level ${level}.</ak-message>`,
            )}`,
        ),
};

export const WithDescription: Story = {
    parameters: describe("`description` adds body text under the title."),
    render: () =>
        container(
            html`<ak-message
                level=${MessageLevel.error}
                .description=${"The server returned 400: the slug is already in use."}
            >
                Failed to save application.
            </ak-message>`,
        ),
};

export const TemplateDescription: Story = {
    parameters: describe("`description` takes a Lit template."),
    render: () =>
        container(
            html`<ak-message
                level=${MessageLevel.warning}
                .description=${html`See <a href="#">the outpost logs</a> for details.`}
            >
                Outpost is out of date.
            </ak-message>`,
        ),
};

export const CustomIcon: Story = {
    parameters: describe("`icon` replaces the level's icon with any Font Awesome class list."),
    render: () =>
        container(
            html`<ak-message level=${MessageLevel.success} icon="fas fa-key">
                Token copied to clipboard.
            </ak-message>`,
        ),
};

export const Dismissible: Story = {
    parameters: describe(
        "`onDismiss` is called by the close button. Here it removes the element. `lifetime` is set to `Infinity`, so there is no timer.",
    ),
    render: () =>
        container(
            html`<ak-message
                id="dismissible"
                lifetime="Infinity"
                .onDismiss=${removeById("dismissible")}
            >
                Click the close button to dismiss me.
            </ak-message>`,
        ),
};

export const AutoDismiss: Story = {
    parameters: describe(
        "With `onDismiss` set, the message is dismissed after `lifetime` ms. This one goes after three seconds; reload the story to see it again.",
    ),
    render: () =>
        container(
            html`<ak-message
                id="auto-dismiss"
                lifetime="3000"
                .onDismiss=${removeById("auto-dismiss")}
            >
                This message disappears in three seconds.
            </ak-message>`,
        ),
};
