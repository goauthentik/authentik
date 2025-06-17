import { searchSelect } from "#tests/utils/controls";

export class RadiusForm {
    async setAuthenticationFlow(buttonText: string) {
        await searchSelect(
            'ak-branded-flow-search[name="authorizationFlow"]',
            "authorizationFlow",
            buttonText,
        );
    }
}

export default new RadiusForm();
