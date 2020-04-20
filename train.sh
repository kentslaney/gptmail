#!/bin/bash
cd "$(dirname "$0")"
bash setup.sh

# clean data
cat data/clean/* | tr -d '\r' > data/all

# create weights directory
mkdir -p weights

# train gpt2
python transformers/examples/run_language_modeling.py \
	--output_dir=${2-weights/default} \
	--overwrite_output_dir \
	--model_type=gpt2 \
	--model_name_or_path=gpt2 \
	--do_train \
	--train_data_file=data/all \
	--save_steps 5000 \
	--num_train_epochs="${1-10}" \
	"$@"
