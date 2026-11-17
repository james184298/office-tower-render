#!/bin/bash
# ad.sh STEP JOBS [PCT] [SAMPLES] [FRAMES] [ENV] [MP4FPS] [FMT] -> prints run id (moonanim.yml)
cd /workspace/work/render/anim
IN=$(jq -cn --arg s "$1" --arg j "$2" --arg p "${3:-25}" --arg q "${4:-4}" --arg f "${5:-1-2012}" --arg e "${6:-}" --arg m "${7:-2}" --arg fm "${8:-JPEG}" \
  '{step:$s,jobs:$j,pct:$p,samples:$q,frames:$f,env:$e,mp4fps:$m,fmt:$fm}')
apicall github workflow_dispatch owner=james184298 repo=office-tower-render workflow_id=moonanim.yml ref=main inputs="$IN" | jq -r '.workflow_run_id // .' | tee last_run.txt
