"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadAppRenderer = loadAppRenderer;
exports.printSSGWarnings = printSSGWarnings;
exports.generateStaticFiles = generateStaticFiles;
const tslib_1 = require("tslib");
const fs_extra_1 = tslib_1.__importDefault(require("fs-extra"));
const path_1 = tslib_1.__importDefault(require("path"));
const lodash_1 = tslib_1.__importDefault(require("lodash"));
// TODO eval is archived / unmaintained: https://github.com/pierrec/node-eval
//  We should internalize/modernize it
const eval_1 = tslib_1.__importDefault(require("eval"));
const p_map_1 = tslib_1.__importDefault(require("p-map"));
const logger_1 = tslib_1.__importStar(require("@docusaurus/logger"));
const bundler_1 = require("@docusaurus/bundler");
const ssgTemplate_1 = require("./ssgTemplate");
const ssgUtils_1 = require("./ssgUtils");
const ssgNodeRequire_1 = require("./ssgNodeRequire");
async function loadAppRenderer({ serverBundlePath, }) {
    const source = await logger_1.PerfLogger.async(`Load server bundle`, () => fs_extra_1.default.readFile(serverBundlePath));
    logger_1.PerfLogger.log(`Server bundle size = ${(source.length / 1024000).toFixed(3)} MB`);
    const filename = path_1.default.basename(serverBundlePath);
    const ssgRequire = (0, ssgNodeRequire_1.createSSGRequire)(serverBundlePath);
    const globals = {
        // When using "new URL('file.js', import.meta.url)", Webpack will emit
        // __filename, and this plugin will throw. not sure the __filename value
        // has any importance for this plugin, just using an empty string to
        // avoid the error. See https://github.com/facebook/docusaurus/issues/4922
        __filename: '',
        // This uses module.createRequire() instead of very old "require-like" lib
        // See also: https://github.com/pierrec/node-eval/issues/33
        require: ssgRequire.require,
    };
    const serverEntry = await logger_1.PerfLogger.async(`Evaluate server bundle`, () => (0, eval_1.default)(source, 
    /* filename: */ filename, 
    /* scope: */ globals, 
    /* includeGlobals: */ true));
    if (!serverEntry?.default || typeof serverEntry.default !== 'function') {
        throw new Error(`Server bundle export from "${filename}" must be a function that renders the Docusaurus React app.`);
    }
    async function shutdown() {
        ssgRequire.cleanup();
    }
    return {
        render: serverEntry.default,
        shutdown,
    };
}
function printSSGWarnings(results) {
    // Escape hatch because SWC is quite aggressive to report errors
    // See https://github.com/facebook/docusaurus/pull/10554
    // See https://github.com/swc-project/swc/discussions/9616#discussioncomment-10846201
    if (process.env.DOCUSAURUS_IGNORE_SSG_WARNINGS === 'true') {
        return;
    }
    const ignoredWarnings = [
        // TODO React/Docusaurus emit NULL chars, and minifier detects it
        //  see https://github.com/facebook/docusaurus/issues/9985
        'Unexpected null character',
    ];
    const keepWarning = (warning) => {
        return !ignoredWarnings.some((iw) => warning.includes(iw));
    };
    const resultsWithWarnings = results
        .map((result) => {
        return {
            ...result,
            warnings: result.warnings.filter(keepWarning),
        };
    })
        .filter((result) => result.warnings.length > 0);
    if (resultsWithWarnings.length) {
        const message = `Docusaurus static site generation process emitted warnings for ${resultsWithWarnings.length} path${resultsWithWarnings.length ? 's' : ''}
This is non-critical and can be disabled with DOCUSAURUS_IGNORE_SSG_WARNINGS=true
Troubleshooting guide: https://github.com/facebook/docusaurus/discussions/10580

- ${resultsWithWarnings
            .map((result) => `${logger_1.default.path(result.pathname)}:
  - ${result.warnings.join('\n  - ')}
`)
            .join('\n- ')}`;
        logger_1.default.warn(message);
    }
}
async function generateStaticFiles({ pathnames, params, }) {
    const [renderer, htmlMinifier, ssgTemplate] = await Promise.all([
        logger_1.PerfLogger.async('Load App renderer', () => loadAppRenderer({
            serverBundlePath: params.serverBundlePath,
        })),
        logger_1.PerfLogger.async('Load HTML minifier', () => (0, bundler_1.getHtmlMinifier)({
            type: params.htmlMinifierType,
        })),
        logger_1.PerfLogger.async('Compile SSG template', () => (0, ssgTemplate_1.compileSSGTemplate)(params.ssgTemplateContent)),
    ]);
    // Note that we catch all async errors on purpose
    // Docusaurus presents all the SSG errors to the user, not just the first one
    const results = await (0, p_map_1.default)(pathnames, async (pathname) => generateStaticFile({
        pathname,
        renderer,
        params,
        htmlMinifier,
        ssgTemplate,
    }).then((result) => ({
        pathname,
        result,
        error: null,
        warnings: result.warnings,
    }), (error) => ({
        pathname,
        result: null,
        error: error,
        warnings: [],
    })), { concurrency: ssgUtils_1.SSGConcurrency });
    await renderer.shutdown();
    printSSGWarnings(results);
    const [allSSGErrors, allSSGSuccesses] = lodash_1.default.partition(results, (result) => !!result.error);
    if (allSSGErrors.length > 0) {
        const message = `Docusaurus static site generation failed for ${allSSGErrors.length} path${allSSGErrors.length ? 's' : ''}:\n- ${allSSGErrors
            .map((ssgError) => logger_1.default.path(ssgError.pathname))
            .join('\n- ')}`;
        // Note logging this error properly require using inspect(error,{depth})
        // See https://github.com/nodejs/node/issues/51637
        throw new Error(message, {
            cause: new AggregateError(allSSGErrors.map((ssgError) => ssgError.error)),
        });
    }
    const collectedData = lodash_1.default.chain(allSSGSuccesses)
        .keyBy((success) => success.pathname)
        .mapValues((ssgSuccess) => ssgSuccess.result.collectedData)
        .value();
    return { collectedData };
}
async function generateStaticFile({ pathname, renderer, params, htmlMinifier, ssgTemplate, }) {
    try {
        // This only renders the app HTML
        const result = await renderer.render({
            pathname,
        });
        // This renders the full page HTML, including head tags...
        const fullPageHtml = (0, ssgTemplate_1.renderSSGTemplate)({
            params,
            result,
            ssgTemplate,
        });
        const minifierResult = await htmlMinifier.minify(fullPageHtml);
        await (0, ssgUtils_1.writeStaticFile)({
            pathname,
            content: minifierResult.code,
            params,
        });
        return {
            collectedData: result.collectedData,
            // As of today, only the html minifier can emit SSG warnings
            warnings: minifierResult.warnings,
        };
    }
    catch (errorUnknown) {
        const error = errorUnknown;
        const tips = getSSGErrorTips(error);
        const message = logger_1.default.interpolate `Can't render static file for pathname path=${pathname}${tips ? `\n\n${tips}` : ''}`;
        throw new Error(message, {
            cause: error,
        });
    }
}
function getSSGErrorTips(error) {
    const parts = [];
    const isNotDefinedErrorRegex = /(?:window|document|localStorage|navigator|alert|location|buffer|self) is not defined/i;
    if (isNotDefinedErrorRegex.test(error.message)) {
        parts.push(`It looks like you are using code that should run on the client-side only.
To get around it, try using one of:
- ${logger_1.default.code('<BrowserOnly>')} (${logger_1.default.url('https://docusaurus.io/docs/docusaurus-core/#browseronly')})
- ${logger_1.default.code('ExecutionEnvironment')} (${logger_1.default.url('https://docusaurus.io/docs/docusaurus-core/#executionenvironment')}).
It might also require to wrap your client code in ${logger_1.default.code('useEffect')} hook and/or import a third-party library dynamically (if any).`);
    }
    return parts.join('\n');
}
