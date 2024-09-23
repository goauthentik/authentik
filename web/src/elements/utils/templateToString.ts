import { type TemplateResult } from "lit";

export function litTemplateToString(template: TemplateResult): string {
    const { strings, values } = template;
    const valuesList = [...values, ""]; // sentinel for ending;
    const result = strings.reduce((acc, s, indx) => {
        const v = valuesList[indx];

        // Value is an embedded template
        if (v._$litType$ !== undefined) {
            return [...acc, s, litTemplateToString(v)];
        }

        // Value is itself a collection
        if (Array.isArray(v)) {
            return [...acc, s, v.map(litTemplateToString).join("")];
        }

        // Value is just a string
        return [...acc, s, v];
    }, []);

    return result.join("");
}

const hasSlot = /^\s*<[^>]*slot="([\w.-]+)"/;

export function getSlot(template: TemplateResult): string | undefined {
    const asString = litTemplateToString(template);
    const g = asString.match(hasSlot);
    return g && g.length > 1 ? g[1] : undefined;
}
