import { createRequire } from "node:module";
import * as path from "node:path";
import * as process from "node:process";
import { fileURLToPath } from "node:url";

/**
 * Predicate to determine if a module was run directly, i.e. not imported.
 *
 * @param {ImportMeta} meta The `import.meta` object of the module.
 *
 * @return {boolean} Whether the module was run directly.
 * @runtime node
 */
export function isMain(meta) {
    // Are we not in a module context?
    if (!meta) return false;

    const relativeScriptPath = process.argv[1];

    if (!relativeScriptPath) return false;

    const require = createRequire(meta.url);
    const absoluteScriptPath = require.resolve(relativeScriptPath);

    const modulePath = fileURLToPath(meta.url);

    const scriptExtension = path.extname(absoluteScriptPath);

    if (scriptExtension) {
        return modulePath === absoluteScriptPath;
    }

    const moduleExtension = path.extname(modulePath);

    if (moduleExtension) {
        return absoluteScriptPath === modulePath.slice(0, -moduleExtension.length);
    }

    // If both are without extension, compare them directly.
    return modulePath === absoluteScriptPath;
}
