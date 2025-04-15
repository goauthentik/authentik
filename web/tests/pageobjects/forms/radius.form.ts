import Page from "../page.js";

export class RadiusForm extends Page {
    async setAuthenticationFlow(selector: string) {
        await this.searchSelect(
            '>>>ak-branded-flow-search[name="authorizationFlow"]',
            "authorizationFlow",
            selector,
        );
    }
}

export default new RadiusForm();
