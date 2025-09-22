import "@patternfly/patternfly/components/Login/login.css";
import "../../stories/flow-interface.js";
import "./FlowErrorStage.js";

import { ContextualFlowInfoLayoutEnum, FrameChallenge, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Stages / <xak-flow-frame>",
};

function flowFrameFactory(challenge: FrameChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme}>
                <xak-flow-frame .challenge=${challenge}></xak-flow-frame>
            </ak-storybook-interface-flow>`;
        },
        args: {
            theme: "automatic",
            challenge: challenge,
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
}

export const NoOverlay = flowFrameFactory({
    flowInfo: {
        title: "<xak-flow-frame>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    url: "https://goauthentik.io",
    loadingText: "loading text",
    loadingOverlay: false,
});

export const Overlay = flowFrameFactory({
    flowInfo: {
        title: "<xak-flow-frame>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    url: "https://goauthentik.io",
    loadingText: "loading text",
    loadingOverlay: true,
});
