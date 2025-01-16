/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import type { Plugin } from 'unified';
import type { Root } from 'mdast';
type PluginOptions = {
    staticDirs: string[];
    siteDir: string;
};
declare const plugin: Plugin<PluginOptions[], Root>;
export default plugin;
//# sourceMappingURL=index.d.ts.map