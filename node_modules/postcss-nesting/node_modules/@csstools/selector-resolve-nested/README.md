# Selector Resolve Nested

[<img alt="npm version" src="https://img.shields.io/npm/v/@csstools/selector-resolve-nested.svg" height="20">][npm-url]
[<img alt="Build Status" src="https://github.com/csstools/postcss-plugins/workflows/test/badge.svg" height="20">][cli-url]
[<img alt="Discord" src="https://shields.io/badge/Discord-5865F2?logo=discord&logoColor=white">][discord]

## API

[Read the API docs](./docs/selector-resolve-nested.md)

## Usage

Add [Selector Resolve Nested] to your project:

```bash
npm install @csstools/selector-resolve-nested --save-dev
```

```js
import { resolveNestedSelector } from '@csstools/selector-resolve-nested';
import parser from 'postcss-selector-parser';

const a = parser().astSync('.foo &');
const b = parser().astSync('.bar');

resolveNestedSelector(a, b); // '.foo .bar'
```

[cli-url]: https://github.com/csstools/postcss-plugins/actions/workflows/test.yml?query=workflow/test
[discord]: https://discord.gg/bUadyRwkJS
[npm-url]: https://www.npmjs.com/package/@csstools/selector-resolve-nested

[Selector Resolve Nested]: https://github.com/csstools/postcss-plugins/tree/main/packages/selector-resolve-nested
