import Page from "../page.js";

export class ScimForm extends Page {
    get url() {
        return $('>>>input[name="url"]');
    }

    get token() {
        return $('>>>input[name="token"]');
    }
}

export default new ScimForm();
