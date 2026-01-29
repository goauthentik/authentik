import "./AccessDeniedStage.js";

import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / Stages / <ak-stage-access-denied>",
};

export const Challenge = flowFactory("ak-stage-access-denied", {
    errorMessage: "This is an error message",
    flowInfo: {
        title: "lorem ipsum foo bar baz",
    },
});
