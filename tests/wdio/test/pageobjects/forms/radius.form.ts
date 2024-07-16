import Page from "../page.js";

export class RadiusForm extends Page {
    async setAuthenticationFlow(selector: string) {
        await this.searchSelect('[name="authorizationFlow"]', "authorizationFlow", `div*=${selector}`);
    }
}

export default new RadiusForm();
