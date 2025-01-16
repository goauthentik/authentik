# html-element-map <sup>[![Version Badge][2]][1]</sup>
Look up HTML tag names via HTML Element constructors, and vice versa.

[![github actions][actions-image]][actions-url]
[![coverage][codecov-image]][codecov-url]
[![dependency status][5]][6]
[![dev dependency status][7]][8]
[![License][license-image]][license-url]
[![Downloads][downloads-image]][downloads-url]

[![npm badge][11]][1]

## Entry points

### `byTag`

```js
const assert = require('assert');
const byTag = require('html-element-map/byTag');
// or: import byTag from 'html-element-map/byTag';
// or: import { byTag } from 'html-element-map';

assert.deepEqual(
		byTag('a'),
		[{
				constructor: window.HTMLAnchorElement,
				constructorName: 'HTMLAnchorElement',
				expectedConstructor: window.HTMLAnchorElement,
				tag: 'a'
		}],
);
```

### `byConstructor`

```js
const assert = require('assert');
const byConstructor = require('html-element-map/byConstructor');
// or: import byConstructor from 'html-element-map/byConstructor';
// or: import { byConstructor } from 'html-element-map';

assert.deepEqual(
		byConstructor(window.HTMLAnchorElement),
		[{
				constructor: window.HTMLAnchorElement,
				constructorName: 'HTMLAnchorElement',
				expectedConstructor: window.HTMLAnchorElement,
				tag: 'a'
		}],
);
```

### `byConstructorName`

```js
const assert = require('assert');
const byConstructorName = require('html-element-map/byConstructorName');
// or: import byConstructorName from 'html-element-map/byConstructorName';
// or: import { byConstructorName } from 'html-element-map';

assert.deepEqual(
		byConstructorName('HTMLAnchorElement'),
		[{
				constructor: window.HTMLAnchorElement,
				constructorName: 'HTMLAnchorElement',
				expectedConstructor: window.HTMLAnchorElement,
				tag: 'a'
		}],
);
```

[1]: https://npmjs.org/package/html-element-map
[2]: https://versionbadg.es/ljharb/html-element-map.svg
[5]: https://david-dm.org/ljharb/html-element-map.svg
[6]: https://david-dm.org/ljharb/html-element-map
[7]: https://david-dm.org/ljharb/html-element-map/dev-status.svg
[8]: https://david-dm.org/ljharb/html-element-map#info=devDependencies
[11]: https://nodei.co/npm/html-element-map.png?downloads=true&stars=true
[license-image]: https://img.shields.io/npm/l/html-element-map.svg
[license-url]: LICENSE
[downloads-image]: https://img.shields.io/npm/dm/html-element-map.svg
[downloads-url]: https://npm-stat.com/charts.html?package=html-element-map
[codecov-image]: https://codecov.io/gh/ljharb/html-element-map/branch/main/graphs/badge.svg
[codecov-url]: https://app.codecov.io/gh/ljharb/html-element-map/
[actions-image]: https://img.shields.io/endpoint?url=https://github-actions-badge-u3jn4tfpocch.runkit.sh/ljharb/html-element-map
[actions-url]: https://github.com/ljharb/html-element-map/actions
