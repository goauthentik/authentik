import { readFileSync, writeFileSync } from "fs";
import path from "path";
import pseudolocale from "pseudolocale";
import { fileURLToPath } from "url";

import { makeFormatter } from "@lit/localize-tools/lib/formatters/index.js";
import type { Message, Placeholder, ProgramMessage } from "@lit/localize-tools/lib/messages.d.ts";
import { sortProgramMessages } from "@lit/localize-tools/lib/messages.js";
import { TransformLitLocalizer } from "@lit/localize-tools/lib/modes/transform.js";
import type { Config } from "@lit/localize-tools/lib/types/config.d.ts";
import type { Locale } from "@lit/localize-tools/lib/types/locale.d.ts";
import type { TransformOutputConfig } from "@lit/localize-tools/lib/types/modes.d.ts";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const pseudoLocale: Locale = "pseudo-LOCALE" as Locale;
const targetLocales: Locale[] = [pseudoLocale];
const baseConfig = JSON.parse(readFileSync(path.join(__dirname, "../lit-localize.json"), "utf8"));

// Need to make some internal specifications to satisfy the transformer. It doesn't actually matter
// which Localizer we use (transformer or runtime), because all of the functionality we care about
// is in their common parent class, but I had to pick one.  Everything else here is just pure
// exploitation of the lit/localize-tools internals.

const config: Config = {
    ...baseConfig,
    baseDir: path.join(__dirname, ".."),
    targetLocales,
    output: {
        ...baseConfig,
        mode: "transform",
    },
    resolve: (path: string) => path,
} as Config;

const pseudoMessagify = (message: ProgramMessage) => ({
    name: message.name,
    contents: message.contents.map((content) =>
        typeof content === "string" ? pseudolocale(content, { prepend: "", append: "" }) : content,
    ),
});

type Translation = { name: string, contents: (string | Placeholder)[] };

const removeDupes = (messages: Translation[]) => {
    const seen = new Map<string, Translation>();
    for (const message of messages) {
        if (!seen.has(message.name)) {
            seen.set(message.name, message);
        } else {
            console.log(`Duplicate detected: ${message.name}`);
        }
    }
    return Array.from(seen.values());
};

const localizer = new TransformLitLocalizer(config as Config & { output: TransformOutputConfig });
const { messages } = localizer.extractSourceMessages();

const translations = removeDupes(messages.map(pseudoMessagify));
const sorted = sortProgramMessages([...messages]);

const formatter = makeFormatter(config);
formatter.writeOutput(sorted, new Map<Locale, Message[]>([[pseudoLocale, translations]]));

// We have this persistent problem where the *formatter* inserts a handful of pseudolocalized lines
// twice, even though they end up with the same ID. This removes those entries the hard way.

function removeXmlDuplicates() {
    const transUnitRe = /<trans-unit id="(s[a-z0-9]+)">/;
    const transCloseRe = /<\/trans-unit>/;
    const seen = new Set<string>();
    const target = path.join(__dirname, "../xliff/pseudo-LOCALE.xlf");
    const pseudoXliff = readFileSync(target, "utf8").split("\n");

	const result = [];
    let inDupe = false;
    for(const line of pseudoXliff) {
        if (inDupe && transCloseRe.test(line)) {
            inDupe = false;
            continue;
        }
        const mTransId = transUnitRe.exec(line);
        if (!mTransId) {
            result.push(line);
            continue;
        }
        const id = mTransId[1];
        if (seen.has(id)) {
            inDupe = true;
            continue;
        }
        seen.add(id);
        result.push(line);
    }

    writeFileSync(target, result.join("\n"), "utf8");
}

removeXmlDuplicates();
