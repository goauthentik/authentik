"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolveMarkdownLinkPathname = resolveMarkdownLinkPathname;
const tslib_1 = require("tslib");
const path_1 = tslib_1.__importDefault(require("path"));
const dataFileUtils_1 = require("./dataFileUtils");
const pathUtils_1 = require("./pathUtils");
// Note this is historical logic extracted during a 2024 refactor
// The algo has been kept exactly as before for retro compatibility
// See also https://github.com/facebook/docusaurus/pull/10168
function resolveMarkdownLinkPathname(linkPathname, context) {
    const { sourceFilePath, sourceToPermalink, contentPaths, siteDir } = context;
    const sourceDirsToTry = [];
    // ./file.md and ../file.md are always relative to the current file
    if (!linkPathname.startsWith('./') && !linkPathname.startsWith('../')) {
        sourceDirsToTry.push(...(0, dataFileUtils_1.getContentPathList)(contentPaths), siteDir);
    }
    // /file.md is never relative to the source file path
    if (!linkPathname.startsWith('/')) {
        sourceDirsToTry.push(path_1.default.dirname(sourceFilePath));
    }
    const aliasedSourceMatch = sourceDirsToTry
        .map((sourceDir) => path_1.default.join(sourceDir, decodeURIComponent(linkPathname)))
        .map((source) => (0, pathUtils_1.aliasedSitePath)(source, siteDir))
        .find((source) => sourceToPermalink.has(source));
    return aliasedSourceMatch
        ? sourceToPermalink.get(aliasedSourceMatch) ?? null
        : null;
}
//# sourceMappingURL=markdownLinks.js.map