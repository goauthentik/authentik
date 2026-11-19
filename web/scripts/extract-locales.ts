/**
 * @remarks
 *   Replaces `lit-localize extract`. See `xliff-plurals.ts` for the plural
 *   group format.
 * @file Extract messages into the XLIFF files, grouping plural forms.
 */

import * as fs from "node:fs/promises";
import path from "node:path";

import { groupPluralUnits, PluralRuntimeLitLocalizer } from "./xliff-plurals.ts";

import { ConsoleLogger } from "#logger/node";
import { PackageRoot } from "#paths/node";

import { readConfigFileAndWriteSchema } from "@lit/localize-tools/lib/config.js";

const logger = ConsoleLogger.child({ name: "Locales" });

const config = readConfigFileAndWriteSchema(path.join(PackageRoot, "lit-localize.json"));

if (config.interchange.format !== "xliff" || config.output.mode !== "runtime") {
    logger.error("Expected XLIFF interchange and runtime output");
    process.exit(1);
}

const localizer = new PluralRuntimeLitLocalizer({
    ...config,
    interchange: config.interchange,
    output: config.output,
});

const { messages, errors } = localizer.extractSourceMessages();

if (errors.length) {
    for (const error of errors) {
        logger.error(error.messageText);
    }

    process.exit(1);
}

logger.info(`Extracted ${messages.length.toLocaleString()} messages`);

await localizer.writeInterchangeFiles();

const xliffDirectory = path.resolve(PackageRoot, config.interchange.xliffDir);
const locales = [config.sourceLocale, ...config.targetLocales];

await Promise.all(
    [...new Set(locales)].map(async (locale) => {
        const filePath = path.join(xliffDirectory, `${locale}.xlf`);
        const xml = await fs.readFile(filePath, "utf8");
        const grouped = groupPluralUnits(xml);

        if (grouped !== xml) {
            await fs.writeFile(filePath, grouped, "utf8");
        }
    }),
);

logger.info("Grouped plural forms");
