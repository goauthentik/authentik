import { $ } from "@wdio/globals";
import Page from "../page.js";

export class ApplicationForm extends Page {
    get name() {
        return $('>>>ak-form-element-horizontal input[name="name"]');
    }
}

export default new ApplicationForm();
