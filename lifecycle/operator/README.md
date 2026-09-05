# authentik operator

A Kubernetes operator that deploys and upgrades authentik. It builds the
Kubernetes objects itself — it does not render or install the Helm chart.

## Why an operator

The [chart](../charts/authentik) already installs authentik. What it cannot do
is control the *order* of an upgrade. `helm upgrade` applies everything at once,
so new pods start migrating the database while old pods are still serving
against the old schema.

The operator closes that window:

1. Resolve which authentik version to deploy, from the spec or from a tracked
   git branch.
2. On an upgrade, run the database migrations to completion in a Job.
3. Only once that Job succeeds, apply the Deployments.

If the migration fails, the Deployments are left alone — the running version
keeps serving, and the resource reports why.

## Relationship to the chart

The objects the operator builds are ports of the chart's templates. Names,
labels and selectors match what the chart produces, so an operator pointed at
an existing chart install adopts it rather than creating a second copy.
`spec` also uses the chart's `values.yaml` key names — `log_level`, `use_tls`,
`secret_key` — so a values file can be moved into `spec` largely unchanged.

`internal/resources/parity_test.go` renders the real chart with `helm template`
and compares object names, the immutable Deployment selectors, and the
configuration Secret's keys against what the builders produce. The chart is the
reference for what is correct; that test is what keeps the two honest.

Two deliberate differences:

| | Chart | Operator |
| --- | --- | --- |
| `AUTHENTIK_ENABLED` | Emitted into the Secret, because `authentik.enabled` sits in the same values block as real options | Not emitted — authentik has no such option |
| PostgreSQL | Bitnami subchart | A StatefulSet the operator builds, so it can be applied in order with everything else |

The chart's `values.yaml` also supplies defaults the CRD does not carry.
Those live in `internal/resources/defaults.go` and in `configDefaults`; several
differ from authentik's own built-in defaults (`error_reporting.environment` is
`k8s` here and `customer` in authentik), so they are reproduced rather than left
to the application.

## The Authentik resource

```yaml
apiVersion: instance.goauthentik.io/v1alpha1
kind: Authentik
metadata:
  name: authentik
spec:
  global:
    image:
      tag: 2026.8.0        # required unless autoUpdate resolves it
  authentik:
    secret_key: <random>
    postgresql:
      password: <password>
  postgresql:
    enabled: true
    auth:
      password: <password>
  server:
    ingress:
      enabled: true
      ingressClassName: nginx
      hosts: [authentik.example.com]
```

See [`config/samples/`](config/samples) for a minimal instance and one that
tracks a branch.

Everything except `releaseName`, `migrations`, `autoUpdate`,
`reconcileInterval` and `prune` is a chart value.

### Status

```console
$ kubectl get authentik
NAME        PHASE   VERSION    OBJECTS   READY   AGE
authentik   Ready   2026.8.0   11        True    5d
```

`phase` is one of `Migrating`, `Deploying`, `Ready`, `Failed`.
Conditions carry the detail: `Ready`, `Progressing`, `Degraded`, `Migrated` and
`Deployed`.

`Ready` describes the instance that is actually serving. During an upgrade it
stays `True` with reason `UpgradePending`, because the previous version is still
up while the migration Job runs.

`status.applied.skipped` names objects whose kind the cluster does not have —
that is how an optional `ServiceMonitor` or `HTTPRoute` reports itself when the
Prometheus Operator or Gateway API CRDs are not installed. Those are skipped
with a warning event rather than failing the reconcile.

### Applying and pruning

Objects are applied with server-side apply under the field owner
`authentik-operator`, with `ForceOwnership`: the operator is the source of truth
for the fields it sets, so a hand-edited Deployment is corrected rather than
blocking reconciles.

When something drops out of the desired state — you disable the Ingress — it is
deleted. Pruning is bounded three ways, because it deletes things:

- only objects labelled `app.kubernetes.io/managed-by: authentik-operator`
  *and* `instance.goauthentik.io/owner: <name>.<namespace>`, so two instances in
  one namespace cannot prune each other, and a Helm-managed object (whose
  `managed-by` is `Helm`) is never a candidate;
- only the kinds listed in `prunableKinds` in `internal/apply/prune.go`. A kind
  absent from that list is never pruned, so disabling a feature leaves its
  object behind — recoverable, unlike the opposite mistake;
- never Jobs. Migration Jobs are meant to outlive a reconcile, so their owner
  reference and TTL clean them up instead.

Set `spec.prune: false` to disable it.

On delete, owner references garbage collect the namespaced objects. The
cluster-scoped RBAC cannot carry an owner reference back to a namespaced
resource, so a finalizer deletes it explicitly. **PersistentVolumeClaims are not
deleted**: Kubernetes never removes a StatefulSet's `volumeClaimTemplates`
volumes, and deleting the database with the resource would be data loss.

### Tracking a branch

```yaml
spec:
  autoUpdate:
    enabled: true
    branch: main
    tagStrategy: Immutable
    interval: 5m
```

authentik's CI publishes two tags per build (see
`.github/actions/compute-container-tags`):

| Tag | Strategy | Behavior |
| --- | --- | --- |
| `gh-<branch>-<timestamp>-<sha>` | `Immutable` (default) | Unique per build, so a new build is a real change to the pod template. Triggers the migration gate and a rollout. |
| `gh-<branch>` | `Branch` | Moving tag; it never changes, so Kubernetes has no reason to replace pods. Only useful with an `Always` pull policy. |

While `autoUpdate` is on, `global.image.tag` is managed by the operator and any
value set there is ignored. If the registry is unreachable, the operator keeps
the deployed version and records a warning rather than failing the instance.

### Migrations

Gating is on by default, and applies only to upgrades: a first install has no
older authentik to be inconsistent with, and the configuration Secret the Job
would read its database credentials from does not exist yet, so the server and
worker migrate on startup as usual.

```yaml
spec:
  migrations:
    enabled: true
    command: [ak, migrate]     # default
    backoffLimit: 3            # pod retries before the Job fails
    activeDeadlineSeconds: 3600
    ttlSecondsAfterFinished: 86400
```

The Job runs the image the Deployments are about to move to, with the same
configuration Secret, and inherits the worker's scheduling settings.

**A failed migration Job is left in place.** Its pods have already been retried
`backoffLimit` times, so the failure is not transient, and deleting the Job
would only restart a migration that is broken. Read its logs, fix the cause, and
the next reconcile creates a new Job — the name is derived from the pod
template, so changing anything the migration depends on is a fresh attempt while
an unrelated change such as a replica count does not re-run migrations.

A Job whose pod cannot start at all (a bad image, an unschedulable pod) never
reaches `JobFailed`, so the operator reports it as `Migrated=False` with reason
`MigrationStuck` and a warning event instead of waiting silently.

## Development

```sh
make build          # build the manager
make run            # run against the current kubeconfig context
make test           # unit tests
make lint           # golangci-lint
```

The parity tests need `helm` on `PATH` and the chart's dependencies vendored:

```sh
helm dependency update ../charts/authentik
```

They skip themselves otherwise, so `make test` works without Helm installed.

### Deploying

```sh
make docker-build docker-push IMG=<registry>/authentik-operator:tag
make install                      # CRDs
make deploy IMG=<registry>/authentik-operator:tag
```

The CRD types the full surface of the chart's values, including Kubernetes' own
volume, affinity, probe and security context types, which makes it ~1.4MB.
Client-side `kubectl apply` stores the whole object in the
`last-applied-configuration` annotation, which is capped at 256KB, so the CRD
**must be applied server-side**. The Makefile targets already pass
`--server-side --force-conflicts`; if you apply the manifests yourself, do the
same.

### Testing against a cluster

Use a throwaway [Kind](https://kind.sigs.k8s.io/) cluster, never a real one —
the operator creates, prunes and deletes objects.

```sh
kind create cluster --name authentik-operator
make install
make run
kubectl apply -k config/samples
```

For a fast end-to-end check of the migration gate without pulling the real
authentik image, point `global.image` at a small image and give `migrations` a
trivial command; the gate logic is exercised the same way.

## Layout

| Path | What it is |
| --- | --- |
| `api/v1alpha1/` | The `Authentik` CRD, its naming rules, and the owner labels pruning selects on |
| `internal/resources/` | The object builders — a port of the chart's templates |
| `internal/apply/` | Server-side apply and label-bounded pruning |
| `internal/version/` | Resolves a git branch to a published container tag |
| `internal/controller/` | Reconciliation, the migration Job, and the gate |
| `config/` | Kustomize manifests: CRD, RBAC, manager, samples |

See [`AGENTS.md`](AGENTS.md) for the conventions this project follows.
