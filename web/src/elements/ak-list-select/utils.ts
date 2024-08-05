import type { GroupedOptions, SelectOptions } from "@goauthentik/elements/types";

export function isVisibleInScrollRegion(el: HTMLElement, container: HTMLElement) {
    const elTop = el.offsetTop;
    const elBottom = elTop + el.clientHeight;
    const containerTop = container.scrollTop;
    const containerBottom = containerTop + container.clientHeight;
    return (
        (elTop >= containerTop && elBottom <= containerBottom) ||
        (elTop < containerTop && containerTop < elBottom) ||
        (elTop < containerBottom && containerBottom < elBottom)
    );
}

export function groupOptions(options: SelectOptions): GroupedOptions {
    return Array.isArray(options) ? { grouped: false, options: options } : options;
}
