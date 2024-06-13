export function findInput(root: Element, tag: string, src: string) {
    const inputs = Array.from(root.querySelectorAll(src));
    if (inputs.length === 0) {
        throw new Error(`${tag}: no element found for 'src' ${src}`);
    }
    if (inputs.length > 1) {
        throw new Error(`${tag}: more than one element found for 'src' ${src}`);
    }
    const input = inputs[0];
    if (!(input instanceof HTMLInputElement)) {
        throw new Error(
            `${tag}: the 'src' element must be an <input> tag, found ${input.localName}`,
        );
    }
    return input;
}

export default findInput;
