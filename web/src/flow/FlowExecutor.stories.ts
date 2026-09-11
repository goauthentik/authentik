import "#flow/stages/dummy/DummyStage";
import "#stories/flow-interface";
import "@patternfly/patternfly/components/Login/login.css";

import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / ak-flow-executor",
};

export const BackgroundImage = flowFactory("ak-stage-dummy");
