---
title: Object Lifecycle Management
description: "Configure authentik to auto-schedule and track periodic reviews of authentication settings for groups, roles, and applications."
sidebar_label: Object Lifecycle Management
authentik_enterprise: true
authentik_version: "2026.2.0"
authentik_preview: true
---

Object Lifecycle Management allows you to automate periodic reviews of authentication settings for groups, roles, and applications.

You can schedule reviews, track progress, and notify reviewers automatically.

## Lifecycle rules

Lifecycle rules define how often reviews are scheduled, the time before a review becomes overdue, who needs to approve a review, and how reviewers are notified.

You can create and configure Lifecycle rules via the **Events** > **Lifecycle Rules** page.

### Rule scope

A lifecycle rule can be scoped to:

- **A specific object**: The rule applies only to that individual Application, Group, or Role.
- **An entire object type**: The rule applies to all objects of that type that don't have their own specific rule, e.g., all applications.

When both a type-level rule and an object-specific rule exist, the object-specific rule takes precedence for that object.

### Rule settings

A lifecycle rule has the following settings:

| Setting                        | Description                                                                                                                                   |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Object type**                | The type of object this rule applies to.                                                                                                      |
| **Object**                     | _(Optional)_ A specific object to apply this rule to. If left empty, the rule applies to all objects of the selected type.                    |
| **Interval**                   | How often reviews are scheduled (e.g., every 60 days). After a review is completed, the next review will be scheduled after this interval.    |
| **Grace period**               | The time period reviewers have to complete the review before it becomes overdue. Must be shorter than the interval.                           |
| **Reviewer groups**            | Groups whose members can submit reviews.                                                                                                      |
| **Min reviewers**              | The minimum number of reviews required from members of any reviewing group.                                                                   |
| **Min reviewers is per group** | When enabled, the minimum number of reviewers is required from each reviewer group separately. When disabled, it's a total across all groups. |
| **Explicit reviewers**         | Individual users who must all submit a review, in addition to the reviewer groups requirement.                                                |
| **Notification transports**    | How reviewers are notified about pending, overdue, and completed reviews.                                                                     |

### Reviewer requirements

An object's review is considered complete when all of the following conditions are met:

1. All explicit reviewers have submitted their reviews.
2. The minimum number of reviews from reviewer group members has been reached (either per group or in total, depending on the setting).

For example, if a rule has:

- Two explicit reviewers (Alice and Bob)
- Two reviewer groups (Security Team and Compliance Team)
- **Min reviewers** is set to 2
- **Min reviewers is per-group** is enabled

Then the review requires approval from: Alice, Bob, at least 2 members of the Security Team, and at least 2 members of the Compliance Team.

## Review states of an object

Each object governed by a lifecycle rule has a review state. You can view all objects with pending or overdue review states on the **Events** > **Reviews** page. You can also view an individual object's current review state on the **Lifecycle** tab of the object's detail page.

| State        | Description                                                                            |
| ------------ | -------------------------------------------------------------------------------------- |
| **Pending**  | A review has been initiated and is waiting for reviewers.                              |
| **Overdue**  | The grace period has passed without the review being completed.                        |
| **Reviewed** | All required reviews have been received and the review is complete.                    |
| **Canceled** | The review was canceled, typically because the lifecycle rule was deleted or modified. |

### Object review workflow

The following steps illustrate the workflow for an object lifecycle review process:

1. When a lifecycle rule is created or when the interval since the last completed review has elapsed, the object enters the **Pending** review state and reviewers are notified.
2. Reviewers submit their reviews (with an optional note).
3. After all requirements are met, the object transitions to the **Reviewed** state.
4. If the grace period passes without all requirements being met, the object becomes **Overdue** and reviewers receive an alert.
5. After the interval passes, a new review cycle begins and the object returns to the **Pending** state.

## Reviewer workflow

To review and approve an object and its associated lifecycle rule, follow the steps below. A reviewer can be either a user set as an explicit reviewer or a member of a configured reviewer group.

1. Once a new review cycle starts for an object, you receive a notification that a review is due (via the configured notification transports).
2. Click on the link in the notification to navigate to the object's detail page.

    Alternatively, you can navigate to the **Events** > **Reviews** page and enable "Only show reviews where I am a reviewer" filter to see objects awaiting your review.
    Here, you can click on the object to navigate to its detail page.

    In both cases, you will be taken to the **Lifecycle** tab of the object's detail page.

3. Review the object's current configuration.
4. Go back to the **Lifecycle** tab.
5. Click **Review** to submit your review, optionally including a note.
6. Once all reviewer requirements are met, the object automatically transitions to the **Reviewed** state.

### Submit a review

When an object is in the **Pending** or **Overdue** review state, authorized reviewers can submit reviews for it. Each reviewer can only submit one review per review cycle. When submitting a review, reviewers can optionally include a note explaining their decision.

Only authorized reviewers can submit reviews:

- Members of the configured reviewer groups
- Users listed as explicit reviewers

### Notifications

Reviewers are notified at the following events:

| Event            | Severity | Description                                                     |
| ---------------- | -------- | --------------------------------------------------------------- |
| Review initiated | Notice   | An object has entered the Pending review state.                 |
| Review overdue   | Alert    | The grace period has passed and the review is still incomplete. |
| Review completed | Notice   | All required reviews have been received.                        |

Configure notification transports on the lifecycle rule to control how these notifications are delivered (UI notification, email, webhook, etc.).
