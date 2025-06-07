import { FlowExecutor } from "@goauthentik/flow/FlowExecutor";

import { customElement } from "lit/decorators.js";

@customElement("ak-storybook-interface-flow")
export class StoryFlowInterface extends FlowExecutor {}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface-flow": StoryFlowInterface;
    }
}
