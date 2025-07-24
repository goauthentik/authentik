import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./AuthenticatorTOTPStage.js";

import { AuthenticatorTOTPChallenge, UiThemeEnum } from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

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
            configUrl:
                "otpauth%3A%2F%2Ftotp%2Fauthentik%3Afoo%3Fsecret%3Dqwerqewrqewrqewrqewr%26algorithm%3DSHA1%26digits%3D6%26period%3D30%26issuer%3Dauthentik%0A",
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
