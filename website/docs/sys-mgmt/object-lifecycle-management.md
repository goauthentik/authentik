---
title: Object Lifecycle Management
sidebar_label: Object Lifecycle Management
authentik_enterprise: true
---

Organizations implementing periodic reviews of their authentication settings for groups, roles, and applications, can configure authentik to automatically schedule and track such reviews, as well as notify the reviewers. This set of functionality is collectively referred to as Object Lifecycle Management.

## Lifecycle rules

You can configure the behavior of reviews for specific object types (currently Applications, Groups, and Roles) or individual objects on the **Events** > **Lifecycle Rules** page.

Lifecycle rules define how often reviews are scheduled, the time before a review goes overdue, who needs to approve a review, and how they are notified.

### Rule scope

A lifecycle rule can be scoped to:

- **A specific object**: The rule applies only to that individual Application, Group, or Role.
- **An entire object type**: The rule applies to all objects of that type that don't have their own specific rule.

When both a type-level rule and an object-specific rule exist, the object-specific rule takes precedence for that object.

### Rule settings

A lifecycle rule has the following settings:

| Setting                            | Description                                                                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Object type**                    | The type of object this rule applies to (Application, Group, or Role).                                                                        |
| **Object**                         | (Optional) A specific object to apply this rule to. If left empty, the rule applies to all objects of the selected type.                      |
| **Interval**                       | How often reviews are scheduled (e.g., every 60 days). After a review is completed, the next review will be scheduled after this interval.    |
| **Grace period**                   | The time period reviewers have to complete the review before it becomes overdue. Must be shorter than the interval.                           |
| **Reviewer groups**                | Groups whose members can attest to reviews.                                                                                                   |
| **Minimum reviewers**              | The minimum number of attestations required from members of any reviewing group.                                                                      |
| **Minimum reviewers is per group** | When enabled, the minimum number of reviewers is required from each reviewer group separately. When disabled, it's a total across all groups. |
| **Explicit reviewers**             | Individual users who must all attest to the review, in addition to the reviewer groups requirement.                                           |
| **Notification transports**        | How reviewers are notified about pending, overdue, and completed reviews.                                                                     |

### Reviewer requirements

A review is considered complete when all of the following conditions are met:

1. All explicit reviewers have attested.
2. The minimum number of attestations from reviewer group members has been reached (either per group or in total, depending on the setting).

For example, if a rule has:

- Two explicit reviewers (Alice and Bob)
- Two reviewer groups (Security Team and Compliance Team)
- **Min** reviewers set to 2
- **Min reviewers is per-group** enabled

Then the review requires attestations from: Alice, Bob, at least 2 members of the Security Team, and at least 2 members of the Compliance Team.

## Reviews

Reviews are automatically created when a lifecycle rule is due. You can view all open reviews on the **Events** > **Access Reviews** page.
You can access an individual object's current review on the **Lifecycle** tab of the object's detail page.

### Review states

| State        | Description                                                                                              |
| ------------ | -------------------------------------------------------------------------------------------------------- |
| **Pending**  | The review has been initiated and is waiting for attestations.                                           |
| **Overdue**  | The grace period has passed without the review being completed. Reviewers receive an alert notification. |
| **Reviewed** | All required attestations have been received and the review is complete.                                 |
| **Canceled** | The review was canceled, typically because the lifecycle rule was deleted or modified.                   |

### Lifecycle

1. When a lifecycle rule is created or when the interval since the last review has elapsed, a new review is automatically created in the **Pending** state.
2. Reviewers are notified that a review is due.
3. Reviewers attest to the review (with an optional note).
4. Once all requirements are met, the review transitions to **Reviewed**.
5. If the grace period passes without completion, the review becomes **Overdue** and reviewers receive an alert.
6. After the interval passes from the review's creation, a new review cycle begins.

## Attestations

An attestation is a record of a reviewer approving a review. Each reviewer can only attest once per review. When creating an attestation, reviewers can optionally include a note explaining their decision.
You can review attestations in the current review for an object as well as create an attestation (provided that you are a reviewer according to the respective rule) on the **Lifecycle** tab of the object's detail page.

Only authorized reviewers can create attestations:

- Members of the configured reviewer groups
- Users listed as explicit reviewers

## Notifications

Reviewers are notified at the following events:

| Event            | Severity | Description                                                     |
| ---------------- | -------- | --------------------------------------------------------------- |
| Review initiated | Notice   | A new review has been created and is pending attestation.       |
| Review overdue   | Alert    | The grace period has passed and the review is still incomplete. |
| Review completed | Notice   | All required attestations have been received.                   |

Configure notification transports on the lifecycle rule to control how these notifications are delivered (UI notification, email, webhook, etc.).
