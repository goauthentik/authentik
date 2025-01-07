"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.getCurrentBundler = getCurrentBundler;
exports.getCurrentBundlerAsRspack = getCurrentBundlerAsRspack;
exports.getCSSExtractPlugin = getCSSExtractPlugin;
exports.getCopyPlugin = getCopyPlugin;
exports.getProgressBarPlugin = getProgressBarPlugin;
const tslib_1 = require("tslib");
const webpack_1 = tslib_1.__importDefault(require("webpack"));
const webpackbar_1 = tslib_1.__importDefault(require("webpackbar"));
const mini_css_extract_plugin_1 = tslib_1.__importDefault(require("mini-css-extract-plugin"));
const copy_webpack_plugin_1 = tslib_1.__importDefault(require("copy-webpack-plugin"));
const importFaster_1 = require("./importFaster");
function isRspack(siteConfig) {
    return siteConfig.future.experimental_faster.rspackBundler;
}
async function getCurrentBundler({ siteConfig, }) {
    if (isRspack(siteConfig)) {
        return {
            name: 'rspack',
            instance: (await (0, importFaster_1.importRspack)()),
        };
    }
    return {
        name: 'webpack',
        instance: webpack_1.default,
    };
}
function getCurrentBundlerAsRspack({ currentBundler, }) {
    if (currentBundler.name !== 'rspack') {
        throw new Error(`Can't getCurrentBundlerAsRspack() because current bundler is ${currentBundler.name}`);
    }
    return currentBundler.instance;
}
async function getCSSExtractPlugin({ currentBundler, }) {
    if (currentBundler.name === 'rspack') {
        // @ts-expect-error: this exists only in Rspack
        return currentBundler.instance.CssExtractRspackPlugin;
    }
    return mini_css_extract_plugin_1.default;
}
async function getCopyPlugin({ currentBundler, }) {
    if (currentBundler.name === 'rspack') {
        // @ts-expect-error: this exists only in Rspack
        return currentBundler.instance.CopyRspackPlugin;
    }
    return copy_webpack_plugin_1.default;
}
async function getProgressBarPlugin({ currentBundler, }) {
    if (currentBundler.name === 'rspack') {
        const rspack = getCurrentBundlerAsRspack({ currentBundler });
        class CustomRspackProgressPlugin extends rspack.ProgressPlugin {
            constructor({ name, color = 'green' }) {
                // Unfortunately rspack.ProgressPlugin does not have name/color options
                // See https://rspack.dev/plugins/webpack/progress-plugin
                super({
                    prefix: name,
                    template: `● {prefix:.bold} {bar:50.${color}/white.dim} ({percent}%) {wide_msg:.dim}`,
                    progressChars: '██',
                });
            }
        }
        return CustomRspackProgressPlugin;
    }
    return webpackbar_1.default;
}
//# sourceMappingURL=currentBundler.js.map