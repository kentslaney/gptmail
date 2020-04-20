# GPTMail
Want to automate a friend? Just download their emails and let GPT-2 do the rest!

This repository just deals with downloading and cleaning the data. [huggingface/transformers](https://github.com/huggingface/transformers) does all of the real work.

If you just want to download weights and run the model, skip to [Downloading Weights](#downloading-weights) and [Using the Web GUI](#using-the-web-gui).

## Downloading Data
### Manually, Individually
By default, this repo assumes that the raw data consists of `.eml` files in `data/raw`. You can download `.eml` files from a number of email clients, but gmail, as an example lets you download individual messages with the "Download message" dropdown option next to the reply button.

### Manually as a Group
Some email clients also allow you to download large numbers of emails as a group using `.mbox` files. For gmail, this can be done using [Google Takeout](https://takeout.google.com). To expand a `.mbox` file into `.eml` files in `data/raw`, run the command
```
$ bash data/mbox.sh path/to/file.eml
```

Note that this will expand all of the emails in the `.mbox`, meaning that in many cases you'll have to delete the `.eml` files of messages you don't want to train on.

### Automatically from gmail
You can also download all of the messages that google returns from a search using Google's Oauth API. Activate the API [here](https://developers.google.com/gmail/api/quickstart/python#step_1_turn_on_the), and download `credentials.json` to the data directory. Then run
```
$ python data/gmail.py "gmail search query"
```

The first time this is run, it will open a browser window to ask you to log in and give permission to the app. Assuming that you haven't asked Google for verification of your API usage, you'll also revieve a warning that the API is unverified. Click "Advanced" and "Continue".

The script also has a number of useful flags that can be seen using
```
$ python data/gmail.py --help
```

## Cleaning Data
The model needs plaintext to read, not `.eml` files, so before training you need to clean the data in `data/raw` and put the results in `data/clean`. For the most part, this can be done automatically with the command
```
$ python data/cleanup.py
```

This will just remove the extra things in the `.eml` files like the metadata, links, and attached files. To further clean the plaintext before training, you can also add extra steps to the cleaning pipeline using python functions. Functions with no arguments add new data to the pipeline, and have to output a list of tuples containing, in order, the output file name and the contents that should be added at that stage of the pipeline. Functions to process data from a previous step should both take and output bytes. As an example, consider the command
```
$ python data/cleanup.py data/examples/hwtaylor/cleanup.py:signature data/cleanup.py:append
```

This relies on two functions: `signature(text)` in `data/examples/hwtaylor/cleanup.py` and `append()` in `data/cleanup.py`. The pipeline first pulls out the plain text in `data/raw/*.eml`, then starts calling the pipeline functions. Because `signature(text)` takes one argument, each of the messages from the previous phase get passed through that function before going to the next stage. In this case, it removes all the email signatures for hwtaylor emails that it can find. The next pipeline phase is `append()` which takes no arguments, meaning that it adds new data to the pipeline. In this case, it outputs all the filenames and contents of files in `data/add`. This way, all of these files are automatically added to the output `data/clean`. If the functions had been flipped, the text from `add` also would have been searched for email signatures, but without being parsed as `.eml` files.

Like `data/gmail.py`, you can find additional flags with the command
```
python data/cleanup.py --help
```

The write at the end of the pipeline ignores any bytes that can't be decoded as UTF-8, so any encoding fixes that need to happen should be part of the pipeline.

## Generating Weights
### Training
To train a model based on the data in `data/clean` for a given number of epochs (`10` here), run
```
$ bash train.sh 10
```

This will output the fine-tuned weights to the `weights/default` directory. Leaving out the number of epochs will cause it to default to 10.

### Downloading Weights
Instead of training your own model, you can also download weights that someone else has created. You can do this by downloading the file, unzipping the archive (`tar xf archive.tar.gz`), and make sure that the unzipped folder is called `weights/default` in the base directory.

Some pretrained models based on sources of potential interest and how they were made:
- [MIT XC snow reports](https://slaney.org/~kent/snowreports.tar.gz)
  - Manual `.eml` download from gmail
  - `python data/cleanup.py`
  - `bash train.sh 10`
- [emails of the famed Halston Taylor](https://slaney.org/~kent/hwtaylor.tar.gz)
  - `python data/gmail.py "from:hwtaylor@mit.edu to:(cross-country@mit.edu OR track-field@mit.edu)"`
  - `python data/examples/hwtaylor/articles.py`
  - `python data/cleanup.py data/examples/hwtaylor/cleanup.py:signature data/cleanup.py:append`
  - `bash train.sh 10`

## Running the Model
### In the Command Line
Running the model based on `weights/default` requires a `length` parameter (1000 here), and a `prompt`:
```
$ bash run.sh 1000 weights/default "This snow report is brought to you by GPT-2."
```

Leaving out the prompt argument will prompt for an input in the CLI.

### Using the Web GUI
Make sure you have all the necessary package requirements by running
```
$ bash setup.sh
```

Then, to serve the web GUI at [http://localhost:8000](http://localhost:8000), simply run
```
python server.py
```

This will serve all the models in the `weights` directory, and picks default prompts at random from `gui/default_prompts`.
