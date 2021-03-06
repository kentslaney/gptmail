#!/bin/bash
cd "$(dirname "$0")"
bash setup.sh

python transformers/examples/run_generation.py \
	--model_type gpt2 \
	--model_name_or_path ${2-weights/default} \
	--length "$1" \
	--prompt "${3-}"
