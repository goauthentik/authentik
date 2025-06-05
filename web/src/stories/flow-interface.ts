import { customElement } from "lit/decorators.js";

import { FlowExecutor } from "../flow/FlowExecutor.js";

@customElement("ak-storybook-interface-flow")
export class StoryFlowInterface extends FlowExecutor {}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface-flow": StoryFlowInterface;
    }
}
