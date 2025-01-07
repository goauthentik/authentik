/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import type { SSGParams } from './ssgParams';
import type { AppRenderer, SiteCollectedData } from '../common';
export declare function loadAppRenderer({ serverBundlePath, }: {
    serverBundlePath: string;
}): Promise<AppRenderer>;
export declare function printSSGWarnings(results: {
    pathname: string;
    warnings: string[];
}[]): void;
export declare function generateStaticFiles({ pathnames, params, }: {
    pathnames: string[];
    params: SSGParams;
}): Promise<{
    collectedData: SiteCollectedData;
}>;
