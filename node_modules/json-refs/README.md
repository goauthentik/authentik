# json-refs

json-refs is a simple library for interacting with [JSON References][json-reference-draft-spec] and
[JSON Pointers][json-pointer-spec].  While the main purpose of this library is to provide JSON References features,
since JSON References are a combination of `Object` structure and a `JSON Pointer`, this library also provides some
features for JSON Pointers as well.

## Project Badges

* Build status: [![Build Status](https://travis-ci.org/whitlockjc/json-refs.svg)](https://travis-ci.org/whitlockjc/json-refs)
* Dependencies: [![Dependencies](https://david-dm.org/whitlockjc/json-refs.svg)](https://david-dm.org/whitlockjc/json-refs)
* Developer dependencies: [![Dev Dependencies](https://david-dm.org/whitlockjc/json-refs/dev-status.svg)](https://david-dm.org/whitlockjc/json-refs#info=devDependencies&view=table)
* Downloads: [![NPM Downloads Per Month](http://img.shields.io/npm/dm/json-refs.svg)](https://www.npmjs.org/package/json-refs)
* Gitter: [![Join the chat at https://gitter.im/whitlockjc/json-refs](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/whitlockjc/json-refs?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
* License: [![License](http://img.shields.io/npm/l/json-refs.svg)](https://github.com/whitlockjc/json-refs/blob/master/LICENSE)
* Version: [![NPM Version](http://img.shields.io/npm/v/json-refs.svg)](https://www.npmjs.org/package/json-refs)

## Documentation

The documentation for this project can be found at <https://github.com/whitlockjc/json-refs/blob/master/docs/README.md>.
Specific documentation can be found here:

* API documentation can be found at <https://github.com/whitlockjc/json-refs/blob/master/docs/API.md>
* CLI can be found at <https://github.com/whitlockjc/json-refs/blob/master/docs/CLI.md>

## Installation

json-refs is available for both Node.js and the browser.  Installation instructions for each environment are below.

### Browser

json-refs binaries for the browser are available in the `dist/` directory:

* [json-refs.js](https://raw.github.com/whitlockjc/json-refs/master/dist/json-refs.js): _2,292kb_, full source source maps
* [json-refs-min.js](https://raw.github.com/whitlockjc/json-refs/master/dist/json-refs-min.js): _148kb_, minified, compressed and no sourcemap

Of course, these links are for the master builds so feel free to download from the release of your choice.  Once you've
gotten them downloaded, to use the standalone binaries, your HTML include might look like this:

``` html
<!-- ... -->
<script src="json-refs.js"></script>
<!-- ... -->
```

### Node.js

Installation for Node.js applications can be done via [NPM][npm].

```
npm install json-refs --save
```

If you plan on using the `json-refs` CLI executable, you can install json-refs globally like this:

```
npm install json-refs --global
```

After this, feel free to run `json-refs help` to see what you can do or view the CLI documentation linked above

[npm]: https://www.npmjs.com/
[json-reference-draft-spec]: http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03
[json-pointer-spec]: http://tools.ietf.org/html/rfc6901
