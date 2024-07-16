import Page from "../page.js";
import { $ } from "@wdio/globals";

export class TransparentProxyForm extends Page {
    async setAuthorizationFlow(selector: string) {
        await this.searchSelect(
            '[name="authorizationFlow"]',
            "authorizationFlow",
            `div*=${selector}`,
        );
    }

    get externalHost() {
        return $('>>>input[name="externalHost"]');
    }

    get internalHost() {
        return $('>>>input[name="internalHost"]');
    }
}

export default new TransparentProxyForm();
