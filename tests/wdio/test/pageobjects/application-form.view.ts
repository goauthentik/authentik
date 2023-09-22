import Page from "./page.js";
import { $ } from "@wdio/globals";

export class ApplicationForm extends Page {
    get name() {
        return $('>>>ak-form-element-horizontal input[name="name"]');
    }
}

export default new ApplicationForm();
