// sort-imports-ignore - Order matters here
/**
 * @file Polyfill entrypoint.
 *
 * Applies side effects to the global scope on import.
 */

import "construct-style-sheets-polyfill";
import "@webcomponents/webcomponentsjs";
import "lit/polyfill-support.js";
import "core-js/actual";

import "@formatjs/intl-listformat/polyfill";
import "@formatjs/intl-listformat/locale-data/en";
