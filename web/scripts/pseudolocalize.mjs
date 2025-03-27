/**
 * @import { Config } from "@lit/localize-tools/lib/types/config.js"
 * @import { TransformOutputConfig } from "@lit/localize-tools/lib/types/modes.js"
 * @import { Locale } from "@lit/localize-tools/lib/types/locale.js"
 * @import { ProgramMessage } from "@lit/localize-tools/lib/messages.js"
 * @import { Message } from "@lit/localize-tools/lib/messages.js"
 *
 * @typedef {Config & { output: TransformOutputConfig; }} TransformerConfig
 */
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import pseudolocale from "pseudolocale";

import { makeFormatter } from "@lit/localize-tools/lib/formatters/index.js";
import { sortProgramMessages } from "@lit/localize-tools/lib/messages.js";
import { TransformLitLocalizer } from "@lit/localize-tools/lib/modes/transform.js";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const pseudoLocale = /** @type {Locale} */ ("pseudo-LOCALE");

const targetLocales = [pseudoLocale];

const baseConfig = await import("../lit-localize.json", {
    with: {
        type: "json",
    },
})
    .then((module) => {
        return /** @type {Config} */ (module.default);
    })

    .catch((error) => {
        console.error("Failed to load lit-localize.json", error);
        process.exit(1);
    });

// Need to make some internal specifications to satisfy the transformer. It doesn't actually matter
// which Localizer we use (transformer or runtime), because all of the functionality we care about
// is in their common parent class, but I had to pick one.  Everything else here is just pure
// exploitation of the lit/localize-tools internals.

/**
 * @type {TransformerConfig}
 */
const config = {
    ...baseConfig,
    baseDir: path.join(__dirname, ".."),
    targetLocales,
    output: {
        ...baseConfig.output,
        mode: "transform",
    },
    resolve: (filePath) => filePath,
};

/**
 * @param {ProgramMessage} message
 * @returns {Message}
 */
function pseudoMessagify({ name, contents }) {
    return {
        name,
        contents: contents.map((content) =>
            typeof content === "string"
                ? pseudolocale(content, { prepend: "", append: "" })
                : content,
        ),
    };
}

const localizer = new TransformLitLocalizer(config);
const { messages } = localizer.extractSourceMessages();
const translations = messages.map(pseudoMessagify);
const sorted = sortProgramMessages([...messages]);
const formatter = makeFormatter(config);

formatter.writeOutput(sorted, new Map([[pseudoLocale, translations]]));
