<h1 align="center">Docusaurus OpenAPI</h1>

<div align="center">

OpenAPI plugin for generating API reference docs in Docusaurus v2.

</div>

<p align="center">

![](https://user-images.githubusercontent.com/4212769/85324376-b9e3d900-b497-11ea-9765-c42a8ad1ff61.png)

</p>

## Multiple OpenAPI Definitions

To have more than one OpenAPI pages, add additional OpenAPI plugin instances:

```js
/* docusaurus.config.js */

{
  presets: [
    [
      'docusaurus-preset-openapi',
      {
        api: {
          // id: 'cars', // omitted => default instance
          path: 'cars/openapi.json',
          routeBasePath: 'cars',
          // ... other options
        },
      },
    ],
  ],
  plugins: [
    [
      'docusaurus-plugin-openapi',
      {
        id: 'trains',
        path: 'trains/openapi.json',
        routeBasePath: 'trains',
        // ... other options
      },
    ],
    [
      'docusaurus-plugin-openapi',
      {
        id: 'bikes',
        path: 'bikes/openapi.json',
        routeBasePath: 'bikes',
        // ... other options
      },
    ],
  ],
}
```

This will create routes for `/cars`, `/trains` and `/bikes`.

> **Note:** One instance of the plugin is included in the preset. All additional plugin instances will require an `id`.
