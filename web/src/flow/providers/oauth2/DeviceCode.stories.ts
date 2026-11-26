import "./DeviceCode.js";
import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / Providers / OAuth2 / <ak-flow-provider-oauth2-code>",
};

export const ChallengeDefault = flowFactory("ak-provider-oauth2-device-code");

export const WithError = flowFactory("ak-provider-oauth2-device-code", {
    responseErrors: {
        code: [{ string: "Invalid code", code: "invalid" }],
    },
});
