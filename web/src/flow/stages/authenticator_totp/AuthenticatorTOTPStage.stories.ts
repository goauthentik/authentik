import "@patternfly/patternfly/components/Login/login.css";
import "./AuthenticatorTOTPStage.js";

import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / Stages / <ak-stage-authenticator-totp>",
};

export const Challenge = flowFactory("ak-stage-authenticator-totp", {
    configUrl:
        "otpauth%3A%2F%2Ftotp%2Fauthentik%3Afoo%3Fsecret%3Dqwerqewrqewrqewrqewr%26algorithm%3DSHA1%26digits%3D6%26period%3D30%26issuer%3Dauthentik%0A",
    flowInfo: {
        title: "Flow title",
    },
});
