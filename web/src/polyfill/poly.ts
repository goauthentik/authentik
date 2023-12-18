import "construct-style-sheets-polyfill";
import "@webcomponents/webcomponentsjs";
import "lit/polyfill-support.js";
import "core-js/actual";

import "@formatjs/intl-listformat/polyfill";
import "@formatjs/intl-listformat/locale-data/en";

if (!("startViewTransition" in document)) {
    // @ts-ignore
    document.startViewTransition = (cb) => {
        cb();
    };
}
