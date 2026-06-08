// sort-imports-ignore
import "@webcomponents/webcomponentsjs";
import "lit/polyfill-support.js";
// `customElements.getName` polyfill — must run before any `customElements.define`
// reaches the registry so the wrapping `define` can populate the reverse map.
// Stays after `@webcomponents/webcomponentsjs` so that on browsers without a
// native registry, the polyfilled one is the object we wrap.
import "./custom-elements-get-name.js";
import "core-js/actual";
import "@formatjs/intl-listformat/polyfill.js";
import "@formatjs/intl-listformat/locale-data/en.js";
