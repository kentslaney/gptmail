import os, random, torch, json, numpy as np
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from flask import Flask, abort, request, render_template
from werkzeug.routing import BaseConverter

relpath = lambda *args: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), *args)
app = Flask(
    __name__, static_folder=relpath("gui"), template_folder=relpath("gui"))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

models = {}
for mname in os.listdir(relpath("weights")):
    mpath = relpath("weights", mname)

    print("loading model {}...".format(mname))
    tokenizer = GPT2Tokenizer.from_pretrained(mpath)
    model = GPT2LMHeadModel.from_pretrained(mpath)
    models[mname] = (tokenizer, model)
    print("moving model {} to {}...".format(mname, device))
    model.to(device)

default_model, default_seed, api_version = "hwtaylor", 42, 1
assert default_model in models and "gui" not in models

class ModelConverter(BaseConverter):
    def to_python(self, model):
        if model not in models:
            abort(404)
        return model
app.url_map.converters['model'] = ModelConverter

def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.device_count() > 0:
        torch.cuda.manual_seed_all(seed)
repetition_penalty, temperature, top_k, top_p = 1.0, 1.0, 0, 0.9

def run(tokenizer, model, prompt, length, sequences):
    encoded_prompt = tokenizer.encode(
        prompt, add_special_tokens=False, return_tensors="pt")
    encoded_prompt = encoded_prompt.to(device)

    output_sequences = model.generate(
        input_ids=encoded_prompt,
        max_length=length + len(encoded_prompt[0]),
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        do_sample=True,
        num_return_sequences=sequences,
    )

    if len(output_sequences.shape) > 2:
        output_sequences.squeeze_()

    generated = []
    for sequence in output_sequences:
        text = tokenizer.decode(
            sequence.tolist(), clean_up_tokenization_spaces=True)
        translated = tokenizer.decode(
            encoded_prompt[0], clean_up_tokenization_spaces=True)
        generated.append(prompt + text[len(translated):])

    return generated

def rebase(value, inbase, outbase):
    output = []
    for remainder in value:
        for digit in range(len(output)):
            remainder = inbase * output[digit] + remainder
            output[digit] = remainder % outbase
            remainder = remainder // outbase
        while remainder:
            output.append(remainder % outbase)
            remainder = remainder // outbase
    return output[::-1]

def translate(value, inalphabet, outalphabet):
    rebased = rebase(map(lambda x: inalphabet.index(x), value),
        len(inalphabet), len(outalphabet))
    return "".join(map(lambda x: outalphabet[x], rebased))

uid = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
digits = "/0123456789"
common = list(map(
    chr, [9, 10, 13] + list(range(32, 47)) + list(range(48, 127)) + [47]))
assert not any(
    c == '/' or c not in common for mname in models.keys() for c in mname)

def to_uid(model, prompt, length, sequences, seed):
    return translate(translate(
        "{}/{}/{}/{}".format(api_version, length, sequences, seed),
        digits, common[:-1]) + "/{}/{}".format(model, prompt), common, uid)

def from_uid(value):
    payload = translate(value, uid, common).split("/", 2)
    config = list(map(
        int, translate(payload[0], common[:-1], digits).split("/")))

    return {
        "model": payload[1], "prompt": payload[2],
        "api_version": config[0], "length": config[1],
        "sequences": config[2], "seed": config[3],
    }

@app.route("/<model:mname>/predict")
def predict(mname):
    prompt, length = request.args.get("p", None), request.args.get("l", None)
    sequences, seed = request.args.get("r", 1), \
        request.args.get("s", default_seed)

    if prompt is None or prompt == "" or length is None:
        abort(400)
    try:
        length, sequences, seed = int(length), int(sequences), int(seed)
    except ValueError:
        abort(400)

    tokenizer, model = models[mname]
    if length > model.config.max_position_embeddings or length <= 0:
        abort(400)

    fpath = relpath("cache", to_uid(mname, prompt, length, sequences, seed))
    if os.path.exists(fpath):
        with open(fpath, "r") as fp:
            return fp.read()
    else:
        set_seed(seed)
        res = json.dumps(run(tokenizer, model, prompt, length, sequences))
        with open(fpath, "w+") as fp:
            fp.write(res)
        return res

client_params = {
    "models": {name: model.config.max_position_embeddings
        for name, (_, model) in models.items()},
    "default_model": default_model,
    "api_version": api_version,
    "default_seed": default_seed,
    "default_length": 200,
}

with open(relpath("gui", "default_prompts"), "r") as fp:
    default_prompts = list(filter(lambda x: x, map(lambda x: x.strip(), fp)))

@app.route("/", defaults={"mname": ""})
@app.route("/<model:mname>")
def index(mname):
    params = {**client_params,
        "model": mname,
        "default_prompt": random.choice(default_prompts),
    }
    return render_template("template.html", params=params)

if __name__ == "__main__":
    if not os.path.exists(relpath("cache")):
        os.mkdir(relpath("cache"))
    app.run(port=8000)
