import Page from "../page.js";
import { $ } from "@wdio/globals";

export class OauthForm extends Page {
    async setAuthorizationFlow(selector: string) {
        await this.searchSelect(
            'ak-flow-search[name="authorizationFlow"]',
            "authorizationFlow",
            `${selector}`,
        );
    }

    async providerName() {
        return await $('ak-form-element-horizontal[name="name"]').$("input");
    }
}

export default new OauthForm();
