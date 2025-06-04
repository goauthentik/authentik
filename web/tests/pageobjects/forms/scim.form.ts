import { $ } from "@wdio/globals";

export abstract class SCIMForm {
    public static get $urlInput() {
        return $('input[name="url"]');
    }

    public static get $tokenInput() {
        return $('input[name="token"]');
    }
}

export default SCIMForm;
