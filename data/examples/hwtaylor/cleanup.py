import re

signature_re = re.compile(rb"(Coach Taylor\s+)?\nHalston W Taylor\nMassachusetts Institute of Technology\nDirector of Track & Field / Cross Country.*", re.DOTALL)

def signature(text):
    return signature_re.sub(b"", text)
