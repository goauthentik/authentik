import Page from "../page.js";

export class RadiusForm extends Page {
    async setAuthenticationFlow(selector: string) {
        await this.searchSelect(
            '>>>ak-branded-flow-search[name="authorizationFlow"] input[type="text"]',
            "authorizationFlow",
            `button*=${selector}`,
        );
    }
}

export default new RadiusForm();
