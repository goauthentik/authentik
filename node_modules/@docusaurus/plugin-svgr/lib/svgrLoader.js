"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createLoader = createLoader;
const utils_1 = require("@docusaurus/utils");
// TODO Docusaurus v4: change these defaults?
//  see https://github.com/facebook/docusaurus/issues/8297
//  see https://github.com/facebook/docusaurus/pull/10205
//  see https://github.com/facebook/docusaurus/pull/10211
const DefaultSVGOConfig = {
    plugins: [
        {
            name: 'preset-default',
            params: {
                overrides: {
                    removeTitle: false,
                    removeViewBox: false,
                },
            },
        },
    ],
};
const DefaultSVGRConfig = {
    prettier: false,
    svgo: true,
    svgoConfig: DefaultSVGOConfig,
    titleProp: true,
};
function createSVGRLoader(params) {
    const options = {
        ...DefaultSVGRConfig,
        ...params.svgrConfig,
    };
    return {
        loader: require.resolve('@svgr/webpack'),
        options,
    };
}
function createLoader(params) {
    const utils = (0, utils_1.getFileLoaderUtils)(params.isServer);
    return {
        test: /\.svg$/i,
        oneOf: [
            {
                use: [createSVGRLoader(params)],
                // We don't want to use SVGR loader for non-React source code
                // ie we don't want to use SVGR for CSS files...
                issuer: {
                    and: [/\.(?:tsx?|jsx?|mdx?)$/i],
                },
            },
            {
                use: [utils.loaders.url({ folder: 'images' })],
            },
        ],
    };
}
