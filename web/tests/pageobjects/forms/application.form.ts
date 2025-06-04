import { $ } from "@wdio/globals";

export abstract class ApplicationForm {
    public static get $name() {
        return $('ak-text-input[name="name"]').$("input");
    }

    public static get $uiSettings() {
        return $("ak-form-group").$('button[aria-label="UI Settings"]');
    }

    public static get $launchURL() {
        return $('input[name="metaLaunchUrl"]');
    }
}

export default ApplicationForm;
