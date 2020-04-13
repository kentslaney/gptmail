import email, re, os, shutil

reply = re.compile(rb"\nOn (Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|June?|July?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?) ([1-2]?[0-9]|3[01]), (19[7-9][0-9]|2[0-9][0-9][0-9]), at (0?[0-9]|1[012]):[0-5][0-9] [AP]M, [^<]+<(?P<email>[^<>@ ]+@[^<>@ ]+.[^<>@ ]+)<mailto:(?P=email)>> wrote:")
formatting = re.compile(rb"<https?://[^ ]+>|\[image: .+?\]|<mailto:[^ ]+>|\[cid:[^ ]+\]")

def clean(fp):
    full = email.message_from_file(fp)
    msg = next((i.get_payload(decode=True) for i in full.walk() \
        if i.get_content_type() == 'text/plain'), None)
    if msg is None:
        raise Exception("No text/plain email encoding")
    quoting = reply.search(msg)
    if quoting is not None:
        msg = msg[:quoting.span()[0]]
    return formatting.sub(b"", msg)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    shutil.rmtree("clean", True)
    os.mkdir("clean")
    for fname in filter(lambda x: x.endswith(".eml"), os.listdir("raw")):
        open(os.path.join("clean", fname[:-4]), "wb+").write(
            clean(open(os.path.join("raw", fname))))
