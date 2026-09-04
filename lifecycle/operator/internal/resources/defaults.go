/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package resources

// The chart supplies these through its values.yaml, which the CRD does not
// carry: a spec field left unset means "use the chart's default", so those
// defaults have to live here instead.
//
// Keep this list in step with lifecycle/charts/authentik/values.yaml. Anything
// that disagrees is a behavior difference between installing the chart and
// running the operator.
const (
	// defaultRevisionHistoryLimit is global.revisionHistoryLimit.
	defaultRevisionHistoryLimit int32 = 3

	// defaultPullPolicy is global.image.pullPolicy.
	defaultPullPolicy = "IfNotPresent"

	// defaultWebPath is authentik.web.path, and prefixes the health endpoints.
	defaultWebPath = "/"

	// defaultReplicas is server.replicas and worker.replicas.
	defaultReplicas int32 = 1

	// defaultTerminationGracePeriod is terminationGracePeriodSeconds.
	defaultTerminationGracePeriod int64 = 30
)

// Server and worker container ports.
const (
	defaultHTTPPort    int32 = 9000
	defaultHTTPSPort   int32 = 9443
	defaultMetricsPort int32 = 9300
)

// Server Service defaults.
const (
	defaultServicePortHTTP      int32 = 80
	defaultServicePortHTTPS     int32 = 443
	defaultServicePortHTTPName        = "http"
	defaultServicePortHTTPSName       = "https"
	defaultNodePortHTTP         int32 = 30080
	defaultNodePortHTTPS        int32 = 30443
	defaultServiceType                = "ClusterIP"
)

// Metrics Service and ServiceMonitor defaults.
const (
	defaultMetricsServicePort int32 = 9300
	defaultMetricsPortName          = "metrics"
	defaultScrapeInterval           = "30s"
	defaultScrapeTimeout            = "3s"
	// metricsPath is where both authentik components expose Prometheus metrics.
	metricsPath = "/metrics"
)

// Ingress defaults.
const defaultPathType = "Prefix"

// Probe defaults, from server.livenessProbe and friends.
const (
	defaultProbeFailureThreshold   int32 = 3
	defaultProbeInitialDelay       int32 = 5
	defaultProbePeriod             int32 = 10
	defaultProbeSuccessThreshold   int32 = 1
	defaultProbeTimeout            int32 = 3
	defaultStartupFailureThreshold int32 = 60
	// The worker's startup probe waits longer, because a worker runs the
	// database migrations before it reports healthy.
	defaultWorkerStartupInitialDelay int32 = 30
)

// GeoIP sidecar defaults.
const (
	defaultGeoIPRepository           = "ghcr.io/maxmind/geoipupdate"
	defaultGeoIPTag                  = "v7.1.1"
	defaultGeoIPEditionIDs           = "GeoLite2-City GeoLite2-ASN"
	defaultGeoIPUpdateInterval int32 = 8
	// geoipVolumeName is the emptyDir the sidecar downloads databases into.
	geoipVolumeName = "geoip-db"
	// geoipMountPath is where authentik reads the databases from, matching
	// authentik.events.context_processors.
	geoipMountPath = "/geoip"
	// geoipDownloadPath is where geoipupdate writes them.
	geoipDownloadPath = "/usr/share/GeoIP"
)

// PostgreSQL defaults. The chart delegates these to the Bitnami subchart; the
// operator runs its own StatefulSet, so it picks equivalents.
const (
	defaultPostgresRegistry         = "docker.io"
	defaultPostgresRepository       = "library/postgres"
	defaultPostgresTag              = "17.11-bookworm"
	defaultPostgresUser             = "authentik"
	defaultPostgresDatabase         = "authentik"
	defaultPostgresPort       int32 = 5432
	defaultPostgresStorage          = "8Gi"
	// defaultPostgresMaxConnections matches the chart's
	// postgresql.primary.extendedConfiguration. authentik holds a connection
	// per worker thread, so the Postgres default of 100 runs out quickly.
	defaultPostgresMaxConnections int32 = 500
	defaultPostgresSecretKey            = "password"
	// postgresDataMount is where the official image expects its data
	// directory, and postgresSubPath keeps PGDATA one level down so the
	// volume's lost+found does not collide with initdb.
	postgresDataMount = "/var/lib/postgresql/data"
	postgresSubPath   = "pgdata"
)

// Blueprint mount paths, from the chart's worker deployment.
const (
	blueprintConfigMapPrefix = "blueprints-cm-"
	blueprintSecretPrefix    = "blueprints-secret-"
	blueprintMountPrefix     = "/blueprints/mounted/"
)

// Component names, matching server.name and worker.name.
const (
	serverComponent = "server"
	workerComponent = "worker"
)

// configChecksumAnnotation restarts the pods when the configuration changes.
// Without it a Secret edit would sit unread until something else replaced the
// pods, which is how the chart behaves too.
const configChecksumAnnotation = "checksum/secret"

// Field names used when building unstructured objects, where there is no Go
// type to spell them for us.
const (
	fieldAPIVersion = "apiVersion"
	fieldKind       = "kind"
	fieldSpec       = "spec"
	fieldPort       = "port"
	fieldPath       = "path"
)

// volumeNameData is the volume and claim name for the database's storage.
const volumeNameData = "data"

// verbList is read-only access, used where the worker only needs to discover
// what a cluster supports.
const verbList = "list"
