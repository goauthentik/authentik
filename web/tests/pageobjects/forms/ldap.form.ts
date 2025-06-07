import { searchSelect } from "#tests/utils/controls";

export abstract class LDAPForm {
    public static setBindFlow() {
        return searchSelect(
            'ak-search-select-view[name="authorizationFlow"]',
            "authorizationFlow",
            "default-authentication-flow",
        );
    }
}

export default LDAPForm;
