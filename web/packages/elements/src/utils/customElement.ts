import { Constructor } from "../types.js";

export function registerCustomElement<T extends Constructor<HTMLElement>>(name: string, Cls: T) {
    if (!window.customElements.get(name)) {
        // eslint-disable-next-line custom-elements/valid-tag-name
        window.customElements.define(name, Cls as Constructor<HTMLElement>);
    }
}
