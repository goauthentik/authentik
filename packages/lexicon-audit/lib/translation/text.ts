import { openLines } from "#translation/files";
import type { TranslationEntry } from "#translation/shared";

/**
 * Read a plain-text file as-is, one entry per non-blank line.
 *
 * Each line is a source string: there is no translation, and no markup is parsed.
 */
export async function* readText(filePath: string): AsyncGenerator<TranslationEntry> {
    using file = openLines(filePath);

    let lineNumber = 0;

    for await (const line of file.lines) {
        lineNumber++;

        if (!line.trim()) {
            continue;
        }

        yield {
            format: "text",
            id: String(lineNumber),
            locale: "",
            line: lineNumber,
            source: line,
            target: "",
        };
    }
}
