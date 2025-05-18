import { Interface } from "@goauthentik/elements/Interface";

import { customElement } from "lit/decorators.js";

@customElement("ak-storybook-interface")
export class StoryInterface extends Interface {}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface": StoryInterface;
    }
}
