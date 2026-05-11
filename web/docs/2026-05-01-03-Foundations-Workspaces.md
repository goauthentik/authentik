# 01 Foundations: Workspaces

Date: 2026-05-02 (May 2st, 2026)

## Workspaces

In order to promote the use and development of a product by the widest community possible, we
default to using NPM workspaces, since it is the most common too possible.

Provide a separate workspace when:

1. The project is support that applies across multiple other workspaces, rather than being a part of
   an application directly. `./packages/core` is the example.
2. The project is a polyfill or library that is needed across all the applications supported by the
   front-end. `./packages/formdata-polyfill` is the example.

3. The project is an application that has radically different requirements from the standard set of
   applications. `./packages/sfe` exists to support only the Login Flow with the Internet Explorer
   11-based rendering engine, which is still embedded in some older Microsoft products we cannot
   afford to ignore.
