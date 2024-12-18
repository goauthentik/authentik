---
title: "Templates"
---

In technical documentation, there are document "types" (similar to how there are data types). We have templates for the different types, to make it super-easy for whomever wants to contribute some documentation!

The most common types are:

- [**Combo**](./combo.md): For most topics (unless they are very large and complex), we can combine the procedural and conceptual information into a single document. A handy guideline to follow is: "If the actual 1., 2., 3. steps are buried at the bottom, and a reader has to scroll multiple times to find them, then the combo approach is _not_ the right one".

- [**Procedural**](./procedural.md): these are How To docs, the HOW information, with step-by-step instructions for accomplishing a task. This is what most people are looking for when they open the docs... and best practice is to separate the procedural docs from long, lengthy conceptual or reference docs.

- [**Conceptual**](./conceptual.md): these docs provide the WHY information, and explain when to use a feature (or when not to!), and general concepts behind the feature or functionality.

- [**Reference**](./reference.md): this is typically tables or lists of reference information, such as configuration values, or functions, or most commmonly APIs.

### Add a new integration

To add documentation for a new integration (with support level Community or Vendor), please use the integration templates [`service.md`](https://github.com/goauthentik/authentik/blob/main/website/integrations/template/service.md) from our GitHub repo. You can download the template using the following command:

```shell
wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/integrations/template/service.md
```
