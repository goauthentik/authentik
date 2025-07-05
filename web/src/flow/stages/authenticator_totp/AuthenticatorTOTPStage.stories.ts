import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import { AuthenticatorTOTPChallenge, UiThemeEnum } from "@goauthentik/api";

import "../../../stories/flow-interface.js";
import "./AuthenticatorTOTPStage";

export default {
    title: "Flow / Stages / <ak-stage-authenticator-totp>",
};

export const Challenge: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-stage-authenticator-totp .challenge=${challenge}></ak-stage-authenticator-totp>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            configUrl: "",
            flowInfo: {
                title: "Flow title",
            },
        } as AuthenticatorTOTPChallenge,
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
