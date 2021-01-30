import email, re

reply = re.compile(
    rb"\n(On (Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|June?|July?|"
    rb"Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?) "
    rb"([1-2]?[0-9]|3[01]), (19[7-9][0-9]|2[0-9][0-9][0-9]), at "
    rb"(0?[0-9]|1[012]):[0-5][0-9] [AP]M, [^<]+<"
    rb"(?P<email>[^<>@ ]+@[^<>@ ]+.[^<>@ ]+)<mailto:(?P=email)>> wrote:|Begin "
    rb"forwarded message:)\n")
formatting = re.compile(
    rb"<https?://[^ ]+>|\[image: .+?\]|<mailto:[^ ]+>|\[cid:[^ ]+\]")

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
