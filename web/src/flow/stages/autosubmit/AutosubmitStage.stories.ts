import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./AutosubmitStage.js";

import { AutosubmitChallenge, ContextualFlowInfoLayoutEnum, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Stages / <ak-stage-autosubmit>",
};

export const StandardChallenge: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-stage-autosubmit .challenge=${challenge}></ak-stage-autosubmit>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            flowInfo: {
                title: "<ak-stage-autosubmit>",
                layout: ContextualFlowInfoLayoutEnum.Stacked,
                cancelUrl: "",
            },
            attrs: {
                foo: "bar",
            },
            url: undefined as unknown as string,
        } as AutosubmitChallenge,
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
