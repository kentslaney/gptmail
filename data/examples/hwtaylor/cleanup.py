import re

signature_re = re.compile(rb"(Coach Taylor\s*)?\s*\n\s*"
    rb"Halston W Taylor\s*\n\s*"
    rb"Massachusetts Institute of Technology\s*\n\s*"
    rb"Director of Track & Field / Cross Country.*", re.DOTALL)

def signature(text):
    return signature_re.sub(b"", text)
