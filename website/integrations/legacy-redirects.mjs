import * as fs from "node:fs/promises";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

import categories from "./categories.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const integrationsDirectory = path.join(__dirname, "..", "integrations");

/**
 * @type {Map<string, string>}
 */
const legacyRedirects = new Map();

for (const [dirName] of categories) {
    const dirPath = path.join(integrationsDirectory, dirName);
    const files = await fs.readdir(dirPath);

    for (const file of files) {
        const filePath = path.join(dirPath, file);
        const fileName = path.basename(filePath);
        const redirectPath = path.join(dirName, fileName);

        legacyRedirects.set(`/services/${fileName}/`, `/${redirectPath}/`);
    }
}

export { legacyRedirects };
