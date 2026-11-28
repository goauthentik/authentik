import { openLines } from "#translation/files";

export interface TSVRow {
    /**
     * 1-based line number in the source file.
     */
    line: number;
    fields: string[];
}

export class TSVError extends Error {
    override name = "TSVError";

    public readonly filePath: string;
    public readonly line: number;

    constructor(filePath: string, line: number, reason: string) {
        // Never include row values; the lexicon content must not reach logs.
        super(`${filePath}:${line}: ${reason}`);
        this.filePath = filePath;
        this.line = line;
    }
}

/**
 * Stream rows from a header-led TSV file with no quoting.
 *
 * Validates the header against `columns` and the field count of every row.
 * Blank lines are skipped.
 */
export async function* readTSV(
    filePath: string,
    columns: readonly string[],
): AsyncGenerator<TSVRow> {
    using file = openLines(filePath);

    let lineNumber = 0;
    let headerSeen = false;

    for await (let line of file.lines) {
        lineNumber++;

        if (lineNumber === 1 && line.startsWith("\uFEFF")) {
            line = line.slice(1);
        }

        if (!line.trim()) {
            continue;
        }

        const fields = line.split("\t");

        if (!headerSeen) {
            if (fields.join("\t") !== columns.join("\t")) {
                throw new TSVError(
                    filePath,
                    lineNumber,
                    `expected header "${columns.join("\\t")}"`,
                );
            }

            headerSeen = true;
            continue;
        }

        if (fields.length !== columns.length) {
            throw new TSVError(
                filePath,
                lineNumber,
                `expected ${columns.length} fields, found ${fields.length}`,
            );
        }

        yield { line: lineNumber, fields };
    }

    if (!headerSeen) {
        throw new TSVError(filePath, lineNumber, "missing header");
    }
}
