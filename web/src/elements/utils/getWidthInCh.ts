export function getWidthInCh(el: HTMLElement) {
    const elementWidthPx = el.getBoundingClientRect().width;

    const temp = document.createElement("div");
    temp.style.position = "absolute";
    temp.style.visibility = "hidden";
    temp.style.width = "1ch";

    const computedStyle = window.getComputedStyle(el);
    temp.style.fontFamily = computedStyle.fontFamily;
    temp.style.fontSize = computedStyle.fontSize;
    temp.style.fontWeight = computedStyle.fontWeight;
    temp.style.fontStyle = computedStyle.fontStyle;

    document.body.appendChild(temp);
    const oneChInPx = temp.getBoundingClientRect().width;
    document.body.removeChild(temp);

    return elementWidthPx / oneChInPx;
}
