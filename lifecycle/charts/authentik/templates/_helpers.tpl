{{/* vim: set filetype=mustache: */}}

{{/*
Create authentik server name and version as used by the chart label.
*/}}
{{- define "authentik.server.fullname" -}}
{{- printf "%s-%s" (include "authentik.fullname" .) .Values.server.name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Get the secret name for authentik configuration
*/}}
{{- define "authentik.secret.name" -}}
{{- if .Values.authentik.existingSecret.secretName -}}
{{- .Values.authentik.existingSecret.secretName -}}
{{- else -}}
{{- template "authentik.fullname" . -}}
{{- end -}}
{{- end -}}

{{/*
Create authentik server worker and version as used by the chart label.
*/}}
{{- define "authentik.worker.fullname" -}}
{{- printf "%s-%s" (include "authentik.fullname" .) .Values.worker.name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Determine the namespace to use, allowing for a namespace override.
*/}}
{{- define "authentik.namespace" -}}
  {{- if .Values.namespaceOverride }}
    {{- .Values.namespaceOverride }}
  {{- else }}
    {{- .Release.Namespace }}
  {{- end }}
{{- end }}

{{/*
Create authentik configuration environment variables.
*/}}
{{- define "authentik.env" -}}
    {{- range $k, $v := .values -}}
        {{- if kindIs "map" $v -}}
            {{- range $sk, $sv := $v -}}
                {{- include "authentik.env" (dict "root" $.root "values" (dict (printf "%s__%s" (upper $k) (upper $sk)) $sv)) -}}
            {{- end -}}
        {{- else -}}
            {{- $value := $v -}}
            {{- if or (kindIs "bool" $v) (kindIs "float64" $v) (kindIs "int" $v) (kindIs "int64" $v) -}}
                {{- $v = $v | toString | b64enc | quote -}}
            {{- else -}}
                {{- $v = tpl (toString $v) $.root | toString | b64enc | quote }}
            {{- end -}}
            {{- if and ($v) (ne $v "\"\"") }}
{{ printf "AUTHENTIK_%s" (upper $k) }}: {{ $v }}
            {{- end }}
        {{- end -}}
    {{- end -}}
{{- end -}}

{{/*
Common deployment strategy definition
- Recreate doesn't have additional fields, we need to remove them if added by the mergeOverwrite
*/}}
{{- define "authentik.strategy" -}}
{{- $preset := . -}}
{{- if (eq (toString $preset.type) "Recreate") }}
type: Recreate
{{- else if (eq (toString $preset.type) "RollingUpdate") }}
type: RollingUpdate
{{- with $preset.rollingUpdate }}
rollingUpdate:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Common affinity definition
Pod affinity
  - Soft prefers different nodes
  - Hard requires different nodes and prefers different availibility zones
Node affinity
  - Soft prefers given user expressions
  - Hard requires given user expressions
*/}}
{{- define "authentik.affinity" -}}
{{- with .component.affinity -}}
  {{- toYaml . -}}
{{- else -}}
{{- $preset := .context.Values.global.affinity -}}
{{- if (eq $preset.podAntiAffinity "soft") }}
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            {{- include "authentik.selectorLabels" (dict "context" .context "component" .component.name) | nindent 12 }}
        topologyKey: kubernetes.io/hostname
{{- else if (eq $preset.podAntiAffinity "hard") }}
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            {{- include "authentik.selectorLabels" (dict "context" .context "component" .component.name) | nindent 12 }}
        topologyKey: topology.kubernetes.io/zone
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          {{- include "authentik.selectorLabels" (dict "context" .context "component" .component.name) | nindent 10 }}
      topologyKey: kubernetes.io/hostname
{{- end }}
{{- with $preset.nodeAffinity.matchExpressions }}
{{- if (eq $preset.nodeAffinity.type "soft") }}
nodeAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 1
      preference:
        matchExpressions:
          {{- toYaml . | nindent 10 }}
{{- else if (eq $preset.nodeAffinity.type "hard") }}
nodeAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    nodeSelectorTerms:
      - matchExpressions:
        {{- toYaml . | nindent 8 }}
{{- end }}
{{- end -}}
{{- end -}}
{{- end -}}
