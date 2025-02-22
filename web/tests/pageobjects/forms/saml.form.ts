import { $ } from "@wdio/globals";

import Page from "../page.js";

export class SamlForm extends Page {
    async setAuthorizationFlow(selector: string) {
        await this.searchSelect(
            '>>>ak-flow-search[name="authorizationFlow"]',
            "authorizationFlow",
            selector,
        );
    }

    get acsUrl() {
        return $('>>>input[name="acsUrl"]');
    }
}

export default new SamlForm();
