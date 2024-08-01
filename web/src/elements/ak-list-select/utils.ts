export function isVisibleInScrollRegion(el, container) {
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
