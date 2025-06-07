/**
 * @file Pseudo-localization script.
 *
 * @import { ConfigFile } from "@lit/localize-tools/lib/types/config.js"
 * @import { Config } from '@lit/localize-tools/lib/types/config.js';
 * @import { ProgramMessage } from "@lit/localize-tools/src/messages.js"
 * @import { Locale } from "@lit/localize-tools/src/types/locale.js"
 */
import { PackageRoot } from "#paths/node";
import { readFileSync } from "node:fs";
import path from "node:path";
import pseudolocale from "pseudolocale";

import { makeFormatter } from "@lit/localize-tools/lib/formatters/index.js";
import { sortProgramMessages } from "@lit/localize-tools/lib/messages.js";
import { TransformLitLocalizer } from "@lit/localize-tools/lib/modes/transform.js";

const pseudoLocale = /** @type {Locale} */ ("pseudo-LOCALE");
const targetLocales = [pseudoLocale];

/**
 * @type {ConfigFile}
 */
const baseConfig = JSON.parse(readFileSync(path.join(PackageRoot, "lit-localize.json"), "utf-8"));

// Need to make some internal specifications to satisfy the transformer. It doesn't actually matter
// which Localizer we use (transformer or runtime), because all of the functionality we care about
// is in their common parent class, but I had to pick one.  Everything else here is just pure
// exploitation of the lit/localize-tools internals.

/**
 * @satisfies {Config}
 */
const config = {
    ...baseConfig,
    baseDir: path.join(__dirname, ".."),
    targetLocales,
    output: {
        ...baseConfig.output,
        mode: "transform",
    },
    resolve: (path) => path,
};

/**
 *
 * @param {ProgramMessage} message
 * @returns
 */
const pseudoMessagify = (message) => ({
    name: message.name,
    contents: message.contents.map((content) =>
        typeof content === "string" ? pseudolocale(content, { prepend: "", append: "" }) : content,
    ),
});

const localizer = new TransformLitLocalizer(config);
const { messages } = localizer.extractSourceMessages();
const translations = messages.map(pseudoMessagify);
const sorted = sortProgramMessages([...messages]);
const formatter = makeFormatter(config);

formatter.writeOutput(sorted, new Map([[pseudoLocale, translations]]));
