{{/* vim: set filetype=mustache: */}}

{{/*
Expand the name of the chart
*/}}
{{- define "authentik.name" -}}
{{- $globalNameOverride := "" -}}
{{- if hasKey .Values "global" -}}
{{- $globalNameOverride = (default $globalNameOverride .Values.global.nameOverride) -}}
{{- end -}}
{{- default .Chart.Name (default .Values.nameOverride $globalNameOverride) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "authentik.fullname" -}}
{{- $name := include "authentik.name" . -}}
{{- $globalFullNameOverride := "" -}}
{{- if hasKey .Values "global" -}}
{{- $globalFullNameOverride = (default $globalFullNameOverride .Values.global.fullnameOverride) -}}
{{- end -}}
{{- if or .Values.fullnameOverride $globalFullNameOverride -}}
{{- $name = default .Values.fullnameOverride $globalFullNameOverride -}}
{{- else -}}
{{- if contains $name .Release.Name -}}
{{- $name = .Release.Name -}}
{{- else -}}
{{- $name = printf "%s-%s" .Release.Name $name -}}
{{- end -}}
{{- end -}}
{{- trunc 63 $name | trimSuffix "-" -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label
*/}}
{{- define "authentik.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create Authentik app version
*/}}
{{- define "authentik.defaultTag" -}}
{{- default .Chart.AppVersion .Values.global.image.tag }}
{{- end -}}

{{/*
Return valid version label
*/}}
{{- define "authentik.versionLabelValue" -}}
{{ regexReplaceAll "[^-A-Za-z0-9_.]" (include "authentik.defaultTag" .) "-" | trunc 63 | trimAll "-" | trimAll "_" | trimAll "." | quote }}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "authentik.labels" -}}
helm.sh/chart: {{ include "authentik.chart" .context | quote }}
{{ include "authentik.selectorLabels" (dict "context" .context "component" .component) }}
app.kubernetes.io/managed-by: {{ .context.Release.Service | quote }}
app.kubernetes.io/part-of: "authentik"
app.kubernetes.io/version: {{ include "authentik.versionLabelValue" .context }}
{{- with .context.Values.global.additionalLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "authentik.selectorLabels" -}}
app.kubernetes.io/name: {{ include "authentik.name" .context | quote }}
app.kubernetes.io/instance: {{ .context.Release.Name | quote }}
{{- if .component }}
app.kubernetes.io/component: {{ .component | quote }}
{{- end }}
{{- end }}
