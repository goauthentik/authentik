import type { Meta, StoryObj } from "@storybook/web-components";

import { LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { type ILoadingOverlay, LoadingOverlay } from "../LoadingOverlay.js";
import "../LoadingOverlay.js";

const metadata: Meta<LoadingOverlay> = {
    title: "Elements/<ak-loading-overlay>",
    component: "ak-loading-overlay",
    parameters: {
        docs: {
            description: "Our empty state spinner",
        },
    },
    argTypes: {
        topmost: { control: "boolean" },
        // @ts-expect-error TODO: Clarify
        message: { control: "text" },
    },
};

export default metadata;

@customElement("ak-storybook-demo-container")
export class Container extends LitElement {
    static get styles() {
        return css`
            :host {
                display: block;
                position: relative;
                height: 25vh;
                width: 75vw;
            }
            #main-container {
                position: relative;
                width: 100%;
                height: 100%;
            }
        `;
    }

    @property({ type: Object, attribute: false })
    content!: TemplateResult;

    render() {
        return html` <div id="main-container">${this.content}</div>`;
    }
}

export const DefaultStory: StoryObj = {
    args: {
        topmost: undefined,
        message: undefined,
    },

    // @ts-expect-error TODO: Clarify
    render: ({ topmost, message }: ILoadingOverlay) => {
        message = typeof message === "string" ? html`<span>${message}</span>` : message;
        const content = html` <ak-loading-overlay ?topmost=${topmost}
            >${message ?? ""}
        </ak-loading-overlay>`;
        return html`<ak-storybook-demo-container
            .content=${content}
        ></ak-storybook-demo-container>`;
    },
};

export const WithAMessage: StoryObj = {
    ...DefaultStory,
    args: { ...DefaultStory.args, message: html`<p>Overlay with a message</p>` },
};
