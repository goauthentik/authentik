import { searchSelect } from "../../utils/controls.js";

export abstract class LDAPForm {
    public static setBindFlow() {
        return searchSelect(
            '>>>ak-search-select-view[name="authorizationFlow"]',
            "authorizationFlow",
            "default-authentication-flow",
        );
    }
}

export default LDAPForm;
