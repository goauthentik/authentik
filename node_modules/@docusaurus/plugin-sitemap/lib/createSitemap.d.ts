/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import type { CreateSitemapItemsParams } from './types';
import type { PluginOptions } from './options';
import type { HelmetServerState } from 'react-helmet-async';
type CreateSitemapParams = CreateSitemapItemsParams & {
    head: {
        [location: string]: HelmetServerState;
    };
    options: PluginOptions;
};
export default function createSitemap(params: CreateSitemapParams): Promise<string | null>;
export {};
