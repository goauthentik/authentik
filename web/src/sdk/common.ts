import { Interface } from "@goauthentik/elements/Interface/Interface";

import { html } from "lit";
import { customElement } from "lit/decorators.js";

import { UiThemeEnum, UiThemeEnumFromJSON } from "@goauthentik/api";

@customElement("ak-sdk-interface")
export class SDKInterface extends Interface {
    constructor() {
        super();
    }
    render() {
        return html`<slot></slot>`;
    }
    async getTheme(): Promise<UiThemeEnum> {
        return UiThemeEnumFromJSON(window.authentik_sdk?.forceTheme) || UiThemeEnum.Automatic;
    }
}
