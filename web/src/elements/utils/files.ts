import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit-html";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";

const FILE_NAME_REPLACEMENTS = ["theme"] as const;

const FILE_NAME_CHARS = "a-zA-Z0-9._/-";
const PLACEHOLDER_PATTERN = FILE_NAME_REPLACEMENTS.join("|");

export const FileNamePattern = {
    /**
     * Used by the {@linkcode assertValidFileName} function to validate file names at runtime. This pattern is stricter than the one used in the HTML pattern attribute, as it does not allow for unescaped parentheses or hyphens.
     */
    Runtime: new RegExp(`^(?:%\\((?:${PLACEHOLDER_PATTERN})\\)s|[${FILE_NAME_CHARS}])+$`),

    /**
     * Used by the HTML pattern attribute. Browsers compile with the `/v` flag,
     * so -, (, and ) must be escaped inside the character class.
     */
    DOM: `^(?:%\\((?:${PLACEHOLDER_PATTERN})\\)s|[a-zA-Z0-9._\\/\\-])+$`,
} as const;

function createListFormatter(localeOrFormatter?: Intl.ListFormat | Intl.LocalesArgument) {
    return localeOrFormatter instanceof Intl.ListFormat
        ? localeOrFormatter
        : new Intl.ListFormat(localeOrFormatter, {
              style: "narrow",
              type: "disjunction",
          });
}

export function formatValidationMessage(
    localeOrFormatter?: Intl.ListFormat | Intl.LocalesArgument,
): string {
    const listFormatter = createListFormatter(localeOrFormatter);

    const replacements = listFormatter.format(
        FILE_NAME_REPLACEMENTS.map((value) => `%(${value})s`),
    );

    return msg(
        str`Valid file names can contain letters, numbers, dots, hyphens, underscores, slashes, and
        placeholders such as ${replacements}.`,
        {
            id: "file.name.validation.plaintext",
            desc: "Validation message for file name input. The placeholders are displayed as plain text.",
        },
    );
}

export function formatHTMLValidationMessage(
    localeOrFormatter?: Intl.ListFormat | Intl.LocalesArgument,
): TemplateResult {
    const listFormatter = createListFormatter(localeOrFormatter);

    const replacements = listFormatter.format(
        FILE_NAME_REPLACEMENTS.map((value) => `<code>%(${value})s</code>`),
    );

    return msg(
        html`Valid file names can contain letters, numbers, dots, hyphens, underscores, slashes, and
        placeholders such as ${unsafeHTML(replacements)}.`,
        {
            id: "file.name.validation.html",
            desc: "Validation message for file name input. The placeholders are displayed as code elements.",
        },
    );
}

export function assertValidFileName(fileName: string): void {
    if (!FileNamePattern.Runtime.test(fileName)) {
        throw new Error(`Invalid file name: ${fileName}. ${formatValidationMessage()}`);
    }
}

export function getFileExtension(fileName: string): string {
    const lastDot = fileName.lastIndexOf(".");

    if (lastDot === -1) return "";

    return fileName.slice(lastDot);
}
