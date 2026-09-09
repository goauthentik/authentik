import { ascii_letters, digits, randomString } from "#common/utils";

export class TabID {
    public static readonly SessionStorageKey = "authentik_tab_id";
    public static readonly shared: TabID = new TabID();

    #id: string;

    constructor() {
        const id = sessionStorage.getItem(TabID.SessionStorageKey);
        const newID = randomString(32, ascii_letters + digits);

        if (id) {
            this.#id = id;
            return;
        }

        this.#id = newID;

        sessionStorage.setItem(TabID.SessionStorageKey, this.#id);
    }

    get current() {
        return this.#id;
    }

    clear() {
        sessionStorage.removeItem(TabID.SessionStorageKey);
    }
}
