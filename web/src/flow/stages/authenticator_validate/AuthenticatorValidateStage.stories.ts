import "@patternfly/patternfly/components/Login/login.css";
import "./AuthenticatorValidateStage.js";

import { flowFactory } from "#stories/flow-interface";

import { DeviceClassesEnum } from "@goauthentik/api";

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

export const MultipleDeviceChallenge = flowFactory("ak-stage-authenticator-validate", {
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
    flowInfo: {
        title: "<ak-stage-authenticator-validate>",
    },
});

export const WebAuthnDeviceChallenge = flowFactory("ak-stage-authenticator-validate", {
    deviceChallenges: [
        {
            deviceClass: DeviceClassesEnum.Webauthn,
            ...webAuthNChallenge,
        },
    ],

    configurationStages: [],
    flowInfo: {
        title: "<ak-stage-authenticator-validate>",
    },
});

export const DuoDeviceChallenge = flowFactory("ak-stage-authenticator-validate", {
    flowInfo: {
        title: "<ak-stage-authenticator-validate>",
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
