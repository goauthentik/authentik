{{/* vim: set filetype=mustache: */}}

{{/*
Expand the name of the chart
*/}}
{{- define "authentik-remote-cluster.name" -}}
{{- $globalNameOverride := "" -}}
{{- if hasKey .Values "global" -}}
{{- $globalNameOverride = (default $globalNameOverride .Values.global.nameOverride) -}}
{{- end -}}
{{- default .Chart.Name (default .Values.nameOverride $globalNameOverride) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Determine the namespace to use, allowing for a namespace override.
*/}}
{{- define "authauthentik-remote-cluster.namespace" -}}
  {{- if .Values.namespaceOverride }}
    {{- .Values.namespaceOverride }}
  {{- else }}
    {{- .Release.Namespace }}
  {{- end }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "authentik-remote-cluster.fullname" -}}
{{- $name := include "authentik-remote-cluster.name" . -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "authentik-remote-cluster.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "authentik-remote-cluster.labels" -}}
helm.sh/chart: {{ include "authentik-remote-cluster.chart" .context | quote }}
app.kubernetes.io/name: {{ include "authentik-remote-cluster.name" .context | quote }}
app.kubernetes.io/instance: {{ .context.Release.Name | quote }}
app.kubernetes.io/managed-by: {{ .context.Release.Service | quote }}
app.kubernetes.io/part-of: "authentik"
app.kubernetes.io/version: {{ .context.Chart.Version | quote }}
{{- with .context.Values.global.additionalLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{- define "authentik-remote-cluster.api-verbs-rw" -}}
- get
- create
- delete
- list
- patch
{{- end -}}
