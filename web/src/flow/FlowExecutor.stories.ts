import "@patternfly/patternfly/components/Login/login.css";
import "../stories/flow-interface.js";
import "./stages/dummy/DummyStage.js";

import { ContextualFlowInfoLayoutEnum, DummyChallenge, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / ak-flow-executor",
};

function flowFactory(challenge: DummyChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme} .challenge=${challenge}>
                <ak-stage-dummy .challenge=${challenge}></ak-stage-dummy>
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

export const BackgroundImage = flowFactory({
    name: "foo",
    flowInfo: {
        title: "<ak-stage-dummy>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
        background: "https://picsum.photos/1920/1080",
    },
});
