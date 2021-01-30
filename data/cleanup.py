import os, argparse, re

relpath = lambda *args: os.path.join(
    os.path.dirname(os.path.abspath(__file__)), *args)

def append():
    parser = argparse.ArgumentParser()
    parser.add_argument("--append", nargs='+', default=(relpath("add"),))
    args, _ = parser.parse_known_args()

    res = []
    for append in args.append:
        for fname in os.listdir(append):
            with open(os.path.join(append, fname), "rb") as fp:
                res.append((fname, fp.read()))
    return res

if __name__ == "__main__":
    import shutil, glob, importlib, inspect
    parser = argparse.ArgumentParser(description="clean up data files")
    parser.add_argument("--input", default=relpath("raw"))
    parser.add_argument("--output", default=relpath("clean"))
    parser.add_argument("--include", default="*")
    parser.add_argument("--remove", default=r"\.eml$")
    parser.add_argument("stages", nargs="*")
    group.add_argument(
        "--no-overwrite", dest="overwrite", action="store_false")
    args, _ = parser.parse_known_args()

    def flist():
        inputs = glob.glob(os.path.join(args.input, args.include))
        return [(re.sub(args.remove, "", os.path.basename(fname)), fname)
                for fname in inputs]

    fopen = lambda fname: open(os.path.join(args.input, fname))
    stages = [(flist, False), (fopen, True)]
    pipeline = lambda stages, value: ((i, x) for i, (x, _) in
        filter(lambda x: x[1][1] == value, enumerate(stages)))

    for stage in args.stages:
        mpath, fname = stage.rsplit(":", 1)
        spec = importlib.util.spec_from_file_location(
            os.path.basename(mpath).rstrip(".py"), mpath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fn = getattr(module, fname)
        stages.append((fn, bool(inspect.getfullargspec(fn).args)))

    if args.overwrite:
        shutil.rmtree(args.output, True)
        os.mkdir(args.output)

    for i, gen in pipeline(stages, False):
        for fname, res in gen():
            for _, pipe in pipeline(stages[i:], True):
                res = pipe(res)
            with open(os.path.join(args.output, fname), "w+") as fp:
                fp.write(res.decode("utf-8", errors="ignore"))
