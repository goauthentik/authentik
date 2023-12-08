export function getRootStyle(selector: string, element: HTMLElement = document.documentElement) {
    return getComputedStyle(element, null).getPropertyValue(selector);
}

export default getRootStyle;
