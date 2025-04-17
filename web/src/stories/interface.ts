import { InterfaceElement } from "@goauthentik/elements/Interface";

import { customElement } from "lit/decorators.js";

@customElement("ak-storybook-interface")
export class StoryInterface extends InterfaceElement {}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface": StoryInterface;
    }
}
