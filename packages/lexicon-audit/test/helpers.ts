/**
 * @file Test fixtures. Every word here is invented or harmless: Jabberwocky and toki pona.
 */

import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";

import { afterEach } from "vitest";

const directories: string[] = [];

afterEach(async () => {
    await Promise.all(
        directories.splice(0).map((dir) => rm(dir, { recursive: true, force: true })),
    );
});

/**
 * Write files into a fresh temporary directory, removed after the test.
 */
export async function fixture(files: Record<string, string>): Promise<string> {
    const root = await mkdtemp(join(tmpdir(), "lexicon-audit-"));

    directories.push(root);

    for (const [path, content] of Object.entries(files)) {
        await mkdir(dirname(join(root, path)), { recursive: true });
        await writeFile(join(root, path), content);
    }

    return root;
}

/**
 * Build a lexicon TSV from `[tier, category, word]` rows.
 */
export function tsv(rows: Array<[string, string, string]>): string {
    return ["tier\tcategory\tword", ...rows.map((row) => row.join("\t"))].join("\n") + "\n";
}

export async function collect<T>(iterable: AsyncIterable<T>): Promise<T[]> {
    const items: T[] = [];

    for await (const item of iterable) {
        items.push(item);
    }

    return items;
}

/**
 * A PO catalog with a header declaring `language`.
 */
export function po(language: string, body: string): string {
    return `msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: ${language}\\n"

${body}`;
}

/**
 * An XLIFF 1.2 document with `units` inside `<body>`.
 */
export function xliff12(targetLanguage: string, units: string): string {
    return `<?xml version="1.0"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
<file target-language="${targetLanguage}" source-language="en" original="test" datatype="plaintext">
<body>
${units}
</body>
</file>
</xliff>
`;
}
