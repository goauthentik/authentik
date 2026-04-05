import "./PasswordStage.js";

import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / Stages / <ak-stage-password>",
};

export const ChallengeDefault = flowFactory("ak-stage-password");

export const WithRecovery = flowFactory("ak-stage-password", {
    recoveryUrl: "foo",
});

export const WithError = flowFactory("ak-stage-password", {
    recoveryUrl: "foo",
    allowShowPassword: true,
    responseErrors: {
        password: [{ string: "nah", code: "nah" }],
    },
});
