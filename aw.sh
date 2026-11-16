#!/bin/bash
# aw.sh RUN : wait up to WAIT s; when complete print render-job logs summary and clone out-RUN into runs/RUN
cd /workspace/work/render/anim; R=$1; T=0
while [ $T -lt ${WAIT:-100} ]; do
  S=$(apicall github workflow_run_get owner=james184298 repo=office-tower-render run_id=$R | jq -r '.status+" "+(.conclusion//"")')
  case "$S" in completed*) break;; esac; sleep 15; T=$((T+15))
done
echo "status: $S"
apicall github workflow_run_jobs_list owner=james184298 repo=office-tower-render run_id=$R | jq -r '.jobs[] | "\(.id) \(.name) \(.status) \(.conclusion) \(.started_at) \(.completed_at)"'
case "$S" in completed*) ;; *) exit 0;; esac
mkdir -p runs/$R
for J in $(apicall github workflow_run_jobs_list owner=james184298 repo=office-tower-render run_id=$R | jq -r '.jobs[] | select(.name|startswith("render")) | .id'); do
  apicall github workflow_job_logs_get owner=james184298 repo=office-tower-render job_id=$J | jq -r '.message // .' > runs/$R/log_$J.txt 2>/dev/null
done
rm -rf runs/$R/out && git clone -q -c http.sslCAInfo="$SSL_CERT_FILE" --depth 1 -b out-$R https://github.com/james184298/office-tower-render.git runs/$R/out 2>/dev/null && ls runs/$R/out | wc -l
