{{/* vim: set filetype=mustache: */}}

{{/*
    Return the target Kubernetes version
*/}}
{{- define "authentik.kubeVersion" -}}
    {{- default .Capabilities.KubeVersion.Version .Values.kubeVersionOverride -}}
{{- end -}}
