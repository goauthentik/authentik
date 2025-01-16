"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeSSG = executeSSG;
const logger_1 = require("@docusaurus/logger");
const ssgParams_1 = require("./ssgParams");
const ssg_1 = require("./ssg");
const ssgTemplate_1 = require("./ssgTemplate");
const ssgUtils_1 = require("./ssgUtils");
// TODO Docusaurus v4 - introduce SSG worker threads
async function executeSSG({ props, serverBundlePath, clientManifestPath, router, }) {
    const params = await (0, ssgParams_1.createSSGParams)({
        serverBundlePath,
        clientManifestPath,
        props,
    });
    if (router === 'hash') {
        logger_1.PerfLogger.start('Generate Hash Router entry point');
        const content = await (0, ssgTemplate_1.renderHashRouterTemplate)({ params });
        await (0, ssgUtils_1.generateHashRouterEntrypoint)({ content, params });
        logger_1.PerfLogger.end('Generate Hash Router entry point');
        return { collectedData: {} };
    }
    const ssgResult = await logger_1.PerfLogger.async('Generate static files', () => (0, ssg_1.generateStaticFiles)({
        pathnames: props.routesPaths,
        params,
    }));
    return ssgResult;
}
