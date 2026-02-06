import { ascii_letters, digits, randomString } from "#common/utils";

export const SESSION_STORAGE_TAB_ID = "authentik_tab_id";

export class TabID {
    static shared: TabID = new TabID();

    #id: string;

    constructor() {
        const id = sessionStorage.getItem(SESSION_STORAGE_TAB_ID);
        const newId = randomString(32, ascii_letters + digits);
        if (id) {
            this.#id = id;
            return;
        }
        this.#id = newId;
        sessionStorage.setItem(SESSION_STORAGE_TAB_ID, this.#id);
    }

    get current() {
        return this.#id;
    }

    clear() {
        sessionStorage.removeItem(SESSION_STORAGE_TAB_ID);
    }
}
