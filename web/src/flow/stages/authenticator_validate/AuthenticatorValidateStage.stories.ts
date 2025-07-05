import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

import "@patternfly/patternfly/components/Login/login.css";

import {
    AuthenticatorValidationChallenge,
    ContextualFlowInfoLayoutEnum,
    DeviceClassesEnum,
    UiThemeEnum,
} from "@goauthentik/api";

import "../../../stories/flow-interface";
import "./AuthenticatorValidateStage";

export default {
    title: "Flow / Stages / <ak-stage-authenticator-validate>",
};

const webAuthNChallenge = {
    deviceUid: "-1",
    challenge: {
        challenge: "qwerqewr",
        timeout: 60000,
        rpId: "localhost",
        allowCredentials: [],
        userVerification: "preferred",
    },
    lastUsed: null,
};

export const MultipleDeviceChallenge: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-stage-authenticator-validate
                .challenge=${challenge}
            ></ak-stage-authenticator-validate>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            flowInfo: {
                title: "<ak-stage-authenticator-validate>",
                layout: ContextualFlowInfoLayoutEnum.Stacked,
                cancelUrl: "",
            },
            deviceChallenges: [
                {
                    deviceClass: DeviceClassesEnum.Duo,
                    deviceUid: "",
                    challenge: {},
                    lastUsed: null,
                },
                {
                    deviceClass: DeviceClassesEnum.Webauthn,
                    ...webAuthNChallenge,
                },
                {
                    deviceClass: DeviceClassesEnum.Totp,
                    deviceUid: "",
                    challenge: {},
                    lastUsed: null,
                },
                {
                    deviceClass: DeviceClassesEnum.Static,
                    deviceUid: "",
                    challenge: {},
                    lastUsed: null,
                },
                {
                    deviceClass: DeviceClassesEnum.Sms,
                    deviceUid: "",
                    challenge: {},
                    lastUsed: null,
                },
                {
                    deviceClass: DeviceClassesEnum.Email,
                    deviceUid: "",
                    challenge: {},
                    lastUsed: null,
                },
            ],
            configurationStages: [],
        } as AuthenticatorValidationChallenge,
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

export const WebAuthnDeviceChallenge: StoryObj = {
    render: ({ theme, challenge }) => {
        return html`<ak-storybook-interface-flow theme=${theme}>
            <ak-stage-authenticator-validate
                .challenge=${challenge}
            ></ak-stage-authenticator-validate>
        </ak-storybook-interface-flow>`;
    },
    args: {
        theme: "automatic",
        challenge: {
            pendingUser: "foo",
            pendingUserAvatar: "https://picsum.photos/64",
            errorMessage: "This is an error message",
            flowInfo: {
                title: "<ak-stage-authenticator-validate>",
                layout: ContextualFlowInfoLayoutEnum.Stacked,
                cancelUrl: "",
            },
            deviceChallenges: [
                {
                    deviceClass: DeviceClassesEnum.Webauthn,
                    ...webAuthNChallenge,
                },
            ],
            configurationStages: [],
        } as AuthenticatorValidationChallenge,
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
