---
title: Deny stage
---

This stage stops the execution of a flow. This can be used to conditionally deny users access to a flow,
even if they are not signed in (and permissions can't be checked via groups).

:::caution
To effectively use this stage, make sure to **disable** _Evaluate on plan_ on the Stage binding.
:::
