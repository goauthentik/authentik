import "@patternfly/patternfly/components/Login/login.css";
import "../../stories/flow-interface.js";
import "./ak-flow-card.js";

import { ContextualFlowInfoLayoutEnum, DummyChallenge, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Components / <ak-flow-card>",
};

export const Empty: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-flow-card .challenge=${challenge}></ak-flow-card>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            flowInfo: {
                title: "lorem ipsum foo bar baz",
                cancelUrl: "",
                layout: ContextualFlowInfoLayoutEnum.Stacked,
            },
            name: "test",
        } as DummyChallenge,
    },
    argTypes: {
        theme: {
            options: [UiThemeEnum.Automatic, UiThemeEnum.Light, UiThemeEnum.Dark],
            control: {
                type: "select",
            },
        },
    },
};

export const Title: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-flow-card .challenge=${challenge} loading>
                <span slot="title">Custom title</span>
            </ak-flow-card>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            flowInfo: {
                title: "lorem ipsum foo bar baz",
                cancelUrl: "",
                layout: ContextualFlowInfoLayoutEnum.Stacked,
            },
            name: "test",
        } as DummyChallenge,
    },
    argTypes: {
        theme: {
            options: [UiThemeEnum.Automatic, UiThemeEnum.Light, UiThemeEnum.Dark],
            control: {
                type: "select",
            },
        },
    },
};

export const EmptyLoading: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-flow-card .challenge=${challenge} loading></ak-flow-card>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            flowInfo: {
                title: "lorem ipsum foo bar baz",
                cancelUrl: "",
                layout: ContextualFlowInfoLayoutEnum.Stacked,
            },
            name: "test",
        } as DummyChallenge,
    },
    argTypes: {
        theme: {
            options: [UiThemeEnum.Automatic, UiThemeEnum.Light, UiThemeEnum.Dark],
            control: {
                type: "select",
            },
        },
    },
};
