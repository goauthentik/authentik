import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./PasswordStage.js";

import { ContextualFlowInfoLayoutEnum, PasswordChallenge, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

export default {
    title: "Flow / Stages / <ak-stage-password>",
};

function passwordFactory(challenge: PasswordChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme}>
                <ak-stage-password .challenge=${challenge}></ak-stage-password>
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

export const ChallengeDefault = passwordFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    flowInfo: {
        title: "<ak-stage-password>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
});

export const WithRecovery = passwordFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    flowInfo: {
        title: "<ak-stage-password>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    recoveryUrl: "foo",
});

export const WithError = passwordFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
    flowInfo: {
        title: "<ak-stage-password>",
        layout: ContextualFlowInfoLayoutEnum.Stacked,
        cancelUrl: "",
    },
    recoveryUrl: "foo",
    allowShowPassword: true,
    responseErrors: {
        password: [{ string: "nah", code: "nah" }],
    },
});
