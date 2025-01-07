# path-loader

Utility that provides a single API for loading the content of a path/URL.  This module works in the browser and in
io.js/Node.js.  Right now this module supports the following loaders:

* http/https: This loader is used by default in the browser and will also be used in io.js/Node.js if the location being
loaded starts with `http:` or `https:`
* file: This loader is the used by default in io.js/Node.js and will throw an error in the browser _(Due to how
locations are mapped to loaders, the only way to use the `file` loader in the browser is to attempt to load a file using
the URL-version of its location.  (Example: `file:///Users/not-you/projects/path-loader/package.json`))_

In the future, there will likely be a pluggable infrastructure for altering this list or overriding the loaders provided
by the project but for now that is not an option.

## Project Badges

* Build status: [![Build Status](https://travis-ci.org/whitlockjc/path-loader.svg)](https://travis-ci.org/whitlockjc/path-loader)
* Downloads: [![NPM Downloads Per Month](http://img.shields.io/npm/dm/path-loader.svg)](https://www.npmjs.org/package/path-loader)
* Gitter: [![Join the chat at https://gitter.im/whitlockjc/path-loader](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/whitlockjc/path-loader?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
* License: [![License](http://img.shields.io/npm/l/path-loader.svg)](https://github.com/whitlockjc/path-loader/blob/master/LICENSE)
* Version: [![NPM Version](http://img.shields.io/npm/v/path-loader.svg)](https://www.npmjs.org/package/path-loader)

## Installation

path-loader is available for both Node.js and the browser.  Installation instructions for each environment are below.

### Browser

path-loader binaries for the browser are available in the `dist/` directory:

* [path-loader.js](https://raw.github.com/whitlockjc/path-loader/master/dist/path-loader.js): _288kb_, full source  and source maps
* [path-loader-min.js](https://raw.github.com/whitlockjc/path-loader/master/dist/path-loader-min.js): _32kb_, minified, compressed and no sourcemap

### Node.js

Installation for Node.js applications can be done via [NPM][npm].

```
npm install path-loader --save
```

## Documentation

The documentation for this project can be found here: https://github.com/whitlockjc/path-loader/blob/master/docs/README.md

The path-loader project's API documentation can be found here: https://github.com/whitlockjc/path-loader/blob/master/docs/API.md

## Dependencies

Below is the list of projects being used by path-loader and the purpose(s) they are used for:

* [native-promise-only][native-promise-only]: Used to shim in [Promises][promises] support
* [superagent][superagent]: AJAX for the browser and Node.js

[native-promise-only]: https://www.npmjs.com/package/native-promise-only
[npm]: https://www.npmjs.org/
[promises]: https://www.promisejs.org/
[superagent]: https://github.com/visionmedia/superagent

