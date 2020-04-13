# GPTMail
Want to automate a friend? Just download their emails, and let GPT-2 do the rest!

This repository just cleans eml files and does some setup. [huggingface/transformers](https://github.com/huggingface/transformers) does all of the real work.
## Usage
Replace the eml files in `data/raw` (unless you want to train on MIT XC snow reports). You can download eml files from gmail via the "Download Message" option. Then run
```
$ bash train.sh
```
which will output the fine-tuned weights to the `weights` directory. Running the model requires a `length` parameter (1000 here), and a `prompt`:
```
$ bash run.sh 1000 "This snow report is brought to you by GPT-2.0."
```
Leaving out the prompt argument will prompt for an input in the CLI.

Depending on the amount of training data, you may want to change the number of epochs in `train.sh`

## Example Weights
You can download the weights outputted by the MIT XC snow reports [here](https://slaney.org/~kent/snowreports.tar.gz). Weights based on the emails of the famed Halston W Taylor soon to come.

Fair warning: each set of GPT-2 weights are ~500MB
