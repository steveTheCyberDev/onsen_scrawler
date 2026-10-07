{{- define "onsen-scrawler.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "onsen-scrawler.labels" -}}
app.kubernetes.io/name: {{ include "onsen-scrawler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "onsen-scrawler.image" -}}
{{ .Values.image.repository }}:{{ .Values.image.tag }}
{{- end -}}

{{/* Pod spec fields shared by the Job and CronJob. Callers add containers[].command/args. */}}
{{- define "onsen-scrawler.podCommon" -}}
restartPolicy: Never
{{- with .Values.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
securityContext:
  {{- toYaml .Values.podSecurityContext | nindent 2 }}
{{- end -}}

{{- define "onsen-scrawler.containerCommon" -}}
image: {{ include "onsen-scrawler.image" . }}
imagePullPolicy: {{ .Values.image.pullPolicy }}
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: {{ .Values.database.existingSecret }}
        key: {{ .Values.database.secretKey }}
securityContext:
  {{- toYaml .Values.containerSecurityContext | nindent 2 }}
resources:
  {{- toYaml .Values.resources | nindent 2 }}
{{- end -}}
