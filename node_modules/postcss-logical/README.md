# PostCSS Logical Properties and Values [<img src="https://postcss.github.io/postcss/logo.svg" alt="PostCSS Logo" width="90" height="90" align="right">][PostCSS]

`npm install postcss-logical --save-dev`

[PostCSS Logical Properties and Values]  lets you use logical, rather than physical, direction and dimension mappings in CSS, following the [CSS Logical Properties and Values] specification.

```pcss
.element {
	block-size: 100px;
	max-inline-size: 400px;
	inline-size: 200px;
	padding-block: 10px 20px;
	margin-inline: auto;
	border-block-width: 2px;
	border-block-style: solid;
}

/* becomes */

.element {
	height: 100px;
	max-width: 400px;
	width: 200px;
	padding-top: 10px;
	padding-bottom: 20px;
	margin-left: auto;
	margin-right: auto;
	border-top-width: 2px;
	border-bottom-width: 2px;
	border-top-style: solid;
	border-bottom-style: solid;
}
```

## Usage

Add [PostCSS Logical Properties and Values] to your project:

```bash
npm install postcss postcss-logical --save-dev
```

Use it as a [PostCSS] plugin:

```js
const postcss = require('postcss');
const postcssLogical = require('postcss-logical');

postcss([
	postcssLogical(/* pluginOptions */)
]).process(YOUR_CSS /*, processOptions */);
```



## Options

### blockDirection & inlineDirection

The `blockDirection` and `inlineDirection` options allow you to specify the direction of the block and inline axes. The default values are `top-to-bottom` and `left-to-right` respectively, which would match any latin language.

**You should tweak these values so that they are specific to your language and writing mode.**

```js
postcssLogical({
	blockDirection: 'right-to-left',
	inlineDirection: 'top-to-bottom'
})
```

```pcss
.element {
	block-size: 100px;
	max-inline-size: 400px;
	inline-size: 200px;
	padding-block: 10px 20px;
	margin-inline: auto;
	border-block-width: 2px;
	border-block-style: solid;
}

/* becomes */

.element {
	width: 100px;
	max-height: 400px;
	height: 200px;
	padding-right: 10px;
	padding-left: 20px;
	margin-top: auto;
	margin-bottom: auto;
	border-right-width: 2px;
	border-left-width: 2px;
	border-right-style: solid;
	border-left-style: solid;
}
```

Each direction must be one of the following:

- `top-to-bottom`
- `bottom-to-top`
- `left-to-right`
- `right-to-left`

You can't mix two vertical directions or two horizontal directions so for example `top-to-bottom` and `right-to-left` are valid, but `top-to-bottom` and `bottom-to-top` are not.

Please do note that `text-align` won't be transformed if `inlineDirection` becomes vertical.

[cli-url]: https://github.com/csstools/postcss-plugins/actions/workflows/test.yml?query=workflow/test
[css-url]: https://cssdb.org/#logical-properties-and-values
[discord]: https://discord.gg/bUadyRwkJS
[npm-url]: https://www.npmjs.com/package/postcss-logical

[PostCSS]: https://github.com/postcss/postcss
[PostCSS Logical Properties and Values]: https://github.com/csstools/postcss-plugins/tree/main/plugins/postcss-logical
[CSS Logical Properties and Values]: https://www.w3.org/TR/css-logical-1/
