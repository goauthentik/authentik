import "@patternfly/patternfly/components/Login/login.css";
import "../../../stories/flow-interface.js";
import "./AuthenticatorValidateStage.js";

import {
    AuthenticatorValidationChallenge,
    ContextualFlowInfoLayoutEnum,
    DeviceClassesEnum,
    UiThemeEnum,
} from "@goauthentik/api";

import type { StoryObj } from "@storybook/web-components";

import { html } from "lit";

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

function authenticatorValidateFactory(challenge: AuthenticatorValidationChallenge): StoryObj {
    return {
        render: ({ theme, challenge }) => {
            return html`<ak-storybook-interface-flow theme=${theme}>
                <ak-stage-authenticator-validate
                    .challenge=${challenge}
                ></ak-stage-authenticator-validate>
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

export const MultipleDeviceChallenge = authenticatorValidateFactory({
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
});

export const WebAuthnDeviceChallenge = authenticatorValidateFactory({
    pendingUser: "foo",
    pendingUserAvatar: "https://picsum.photos/64",
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
});

export const DuoDeviceChallenge = authenticatorValidateFactory({
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
            deviceUid: "1",
            challenge: {},
            lastUsed: null,
        },
    ],
    configurationStages: [],
});
