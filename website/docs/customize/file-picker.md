---
title: File picker values
authentik_version: "2025.12"
---

Many fields in the authentik Admin interface use the same file picker. You can use it to select an uploaded file, reference a built-in static asset, point at an external URL, or use a Font Awesome icon.

This applies to:

- **System** > **Brands** > **Logo**
- **System** > **Brands** > **Favicon**
- **System** > **Brands** > **Default flow background**
- **Flows and Stages** > **Flows** > **Background**
- **Applications** > **Applications** > **Icon**
- **Applications** > **New Application** wizard > **Icon**
- **Directory** > **Federation and Social login** > source **Icon** fields for SAML, OAuth, Plex, and Kerberos sources

## Accepted values

The file picker accepts the following value types.

| Value type            | Example                                         | Notes                                                                                                                                                                                                                         |
| --------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Uploaded file path    | `branding/company-logo.svg`                     | Relative path to a file stored in authentik's media storage. You can upload these from **Customization** > **Files**. When authentik serves these files, it uses a short-lived protected URL rather than a fixed public path. |
| Built-in static asset | `/static/dist/assets/icons/icon_left_brand.svg` | Absolute path to a built-in asset shipped with authentik.                                                                                                                                                                     |
| External URL          | `https://cdn.example.com/branding/logo.svg`     | Useful when files are hosted outside authentik.                                                                                                                                                                               |
| Font Awesome icon     | `fa://fa-circle-user`                           | Supported for icon fields. See [Font Awesome icons](#font-awesome-icons) for syntax, supported families, and usage notes. This is not useful for background image fields.                                                     |

When you open the picker, authentik lists uploaded files and built-in static assets. You can also type a custom value directly into the field.

## Font Awesome icons

Use Font Awesome values only in icon fields such as application icons, source icons, and similar picker-backed icon settings. They are not useful for logo or background image fields.

The simplest format is `fa://<icon>`. If you omit the family, authentik uses Font Awesome Solid.

Examples:

- `fa://fa-shield-halved`
- `fa://shield-halved`
- `fa://fa-circle-user`

To choose a specific family, use `fa://<family>/<icon>`. The icon name can include or omit the `fa-` prefix.

Examples:

- `fa://brands/fa-google`
- `fa://fab/fa-linkedin`
- `fa://regular/fa-circle-user`
- `fa://light/fa-coffee`
- `fa://sharp-solid/fa-check`

authentik also accepts raw Font Awesome class syntax, such as `fa://fab fa-github`, when you already have the class list and want to pass it through directly.

Supported family prefixes:

| Family                | Aliases                                                      | Resulting classes             |
| --------------------- | ------------------------------------------------------------ | ----------------------------- |
| Solid                 | `solid`, `fas`, `fa-solid`                                   | `fa-solid`                    |
| Regular               | `regular`, `far`, `fa-regular`                               | `fa-regular`                  |
| Brands                | `brands`, `fab`, `fa-brands`                                 | `fa-brands`                   |
| Light                 | `light`, `fal`, `fa-light`                                   | `fa-light`                    |
| Thin                  | `thin`, `fat`, `fa-thin`                                     | `fa-thin`                     |
| Duotone               | `duotone`, `fad`, `fa-duotone`                               | `fa-duotone`                  |
| Sharp solid           | `sharp-solid`, `fass`, `fa-sharp-solid`                      | `fa-sharp fa-solid`           |
| Sharp regular         | `sharp-regular`, `fasr`, `fa-sharp-regular`                  | `fa-sharp fa-regular`         |
| Sharp light           | `sharp-light`, `fasl`, `fa-sharp-light`                      | `fa-sharp fa-light`           |
| Sharp thin            | `sharp-thin`, `fast`, `fa-sharp-thin`                        | `fa-sharp fa-thin`            |
| Sharp duotone solid   | `sharp-duotone-solid`, `fasds`, `fa-sharp-duotone-solid`     | `fa-sharp-duotone fa-solid`   |
| Sharp duotone regular | `sharp-duotone-regular`, `fasdr`, `fa-sharp-duotone-regular` | `fa-sharp-duotone fa-regular` |
| Sharp duotone light   | `sharp-duotone-light`, `fasdl`, `fa-sharp-duotone-light`     | `fa-sharp-duotone fa-light`   |
| Sharp duotone thin    | `sharp-duotone-thin`, `fasdt`, `fa-sharp-duotone-thin`       | `fa-sharp-duotone fa-thin`    |

authentik ships the Font Awesome Free styles needed for `solid`, `regular`, and `brands`. The Pro families, such as `light`, `thin`, `duotone`, and the sharp variants, work when you load the matching Font Awesome Pro CSS yourself, for example through a Kit embed or [brand custom CSS](../sys-mgmt/brands/custom-css.mdx). authentik does not bundle Font Awesome Pro; it only passes the requested family classes through to the rendered icon.

## Theme-aware values with `%(theme)s`

Some assets can change based on whether the active theme is light or dark. For those cases, you can use the placeholder `%(theme)s` in the path or URL.

Examples:

- `branding/logo-%(theme)s.svg`
- `branding/background-%(theme)s.jpg`
- `/static/dist/assets/icons/icon-%(theme)s.svg`
- `https://cdn.example.com/assets/logo-%(theme)s.svg`

authentik resolves `%(theme)s` to:

- `light`
- `dark`

`automatic` is not substituted directly. When a user is set to automatic theme selection, authentik chooses either the light or dark asset first and then uses the matching resolved URL.

This resolution happens on the backend, which means it also works with storage backends that need signed URLs, such as S3.

The `%(theme)s` placeholder is supported in all current Admin UI fields that use the shared file picker:

- Brand **Logo**
- Brand **Favicon**
- Brand **Default flow background**
- Flow **Background**
- Application **Icon**
- Source **Icon**

## Upload and path rules

When uploading a file in **Customization** > **Files**, or when typing a relative media path manually, use these rules:

- If a file exists at `/data/media/public/branding/logo.svg`, enter `branding/logo.svg` in the picker field - without a leading slash. Do not enter `/data/media/public/branding/logo.svg` or `/branding/logo.svg`.
- Files uploaded through **Customization** > **Files** are always served through a temporary protected URL
- On S3 storage, authentik generates a presigned S3 URL
- On local file storage, authentik generates an authentik `/files/...` URL with a unique signed token
- Uploaded files can be up to 25 MB each
- Allowed characters are letters, numbers, `.`, `_`, `-`, and `/`
- `%(theme)s` is also allowed anywhere in the path
- Paths must be relative, not absolute
- Parent directory references such as `..` are not allowed
- Duplicate slashes such as `//` are not allowed
- Paths cannot start with `.`
- The full path can be up to 1024 characters long
- Each path segment can be up to 255 characters long

Examples of valid upload names:

- `branding/logo.svg`
- `branding/logo-%(theme)s.svg`
- `sources/oauth/company-icon.png`

If you rename a file during upload, authentik keeps the original file extension.
