#!/bin/bash
cd "$(dirname "$0")"

# install transformers
if [ ! -d "transformers" ]; then
	git clone https://github.com/huggingface/transformers
fi

python -m pip install tensorflow torch | grep -v "Requirement already satisfied"
python -m pip install -r transformers/examples/requirements.txt | \
    grep -v "Requirement already satisfied"

if [[ ! $(pip list | grep transformers) ]]; then
	  python -m pip install -e transformers | \
        grep -v "Requirement already satisfied"
fi
