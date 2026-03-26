import "@patternfly/patternfly/components/Login/login.css";
import "./AutosubmitStage.js";

import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / Stages / <ak-stage-autosubmit>",
};

export const StandardChallenge = flowFactory("ak-stage-autosubmit", {
    attrs: {
        foo: "bar",
    },
});
