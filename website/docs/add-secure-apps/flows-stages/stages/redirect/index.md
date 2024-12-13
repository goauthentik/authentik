---
title: Redirect stage
---

<span class="badge badge--version">authentik 2024.12+</span>

---

This stage's main purpose is to redirect the user to a new Flow while keeping flow context. For convenience, it can also redirect the user to a static URL.

## Redirect stage modes

### Static mode

When the user reaches this stage, they are redirected to a static URL.

### Flow mode

When the user reaches this stage, they are redirected to a specified flow, retaining all [flow context](../../flow/context).

Optionally, untoggle the "Keep flow context" switch. If this is untoggled, all flow context is cleared with the exception of the [is_redirected](../../flow/context#is_redirected-flow-object-authentik-202412) key.
