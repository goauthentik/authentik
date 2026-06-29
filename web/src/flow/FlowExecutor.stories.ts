import "@patternfly/patternfly/components/Login/login.css";
import "#stories/flow-interface";
import "#flow/stages/dummy/DummyStage";

import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / ak-flow-executor",
};

export const BackgroundImage = flowFactory("ak-stage-dummy");
