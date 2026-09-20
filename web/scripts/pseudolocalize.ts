/**
 * @file Pseudo-localization script.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { PackageRoot } from "#paths/node";

import { isMain } from "@goauthentik/core/scripting/node";

import pseudolocale from "pseudolocale";

import { makeFormatter } from "@lit/localize-tools/lib/formatters/index.js";
import type { Message, ProgramMessage } from "@lit/localize-tools/lib/messages.js";
import { sortProgramMessages } from "@lit/localize-tools/lib/messages.js";
import { TransformLitLocalizer } from "@lit/localize-tools/lib/modes/transform.js";
import type { Config, ConfigFile } from "@lit/localize-tools/lib/types/config.js";
import type { Locale } from "@lit/localize-tools/lib/types/locale.js";
import type { TransformOutputConfig } from "@lit/localize-tools/lib/types/modes.js";

const pseudoLocale = "en-XA" as Locale;
const targetLocales = [pseudoLocale];
const __dirname = fileURLToPath(new URL(".", import.meta.url));

const baseConfig = JSON.parse(
    readFileSync(path.join(PackageRoot, "lit-localize.json"), "utf-8"),
) as ConfigFile;

// Need to make some internal specifications to satisfy the transformer. It doesn't actually matter
// which Localizer we use (transformer or runtime), because all of the functionality we care about
// is in their common parent class, but I had to pick one.  Everything else here is just pure
// exploitation of the lit/localize-tools internals.

const config: Config & { output: TransformOutputConfig } = {
    ...baseConfig,
    baseDir: path.join(__dirname, ".."),
    targetLocales,
    output: {
        ...baseConfig.output,
        mode: "transform",
    },
    resolve: (path: string) => path,
};

const pseudoMessagify = (message: ProgramMessage): Message => ({
    name: message.name,
    contents: message.contents.map((content) =>
        typeof content === "string" ? pseudolocale(content, { prepend: "", append: "" }) : content,
    ),
});

export async function generatePseudoLocaleModule() {
    const localizer = new TransformLitLocalizer(config);
    const { messages } = localizer.extractSourceMessages();
    const translations = messages.map(pseudoMessagify);
    const sorted = sortProgramMessages([...messages]);
    const formatter = makeFormatter(config);

    await formatter.writeOutput(sorted, new Map([[pseudoLocale, translations]]));
}

if (isMain(import.meta)) {
    generatePseudoLocaleModule();
}
