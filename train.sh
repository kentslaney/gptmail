#!/bin/bash
cd "$(dirname "$0")"
bash setup.sh

# clean data
find "{$2-data/clean}" -type f | xargs cat | tr -d '\r' > data/all

# create weights directory
mkdir -p weights

# train gpt2
epochs="${1-10}"; shift
out="${1-weights/default}"; shift
python transformers/examples/run_language_modeling.py \
	--output_dir="$out" \
	--overwrite_output_dir \
	--model_type=gpt2 \
	--model_name_or_path=gpt2 \
	--do_train \
	--train_data_file=data/all \
	--save_steps=5000 \
	--num_train_epochs="$epochs" \
	"$@"
