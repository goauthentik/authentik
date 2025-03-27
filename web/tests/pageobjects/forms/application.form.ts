import { $ } from "@wdio/globals";

import Page from "../page.js";

export class ApplicationForm extends Page {
    name() {
        return $('>>>ak-text-input[name="name"]').$(">>>input");
    }

    uiSettings() {
        return $(">>>ak-form-group").$('button[aria-label="UI Settings"]');
    }

    launchUrl() {
        return $('>>>input[name="metaLaunchUrl"]');
    }
}

export default new ApplicationForm();
