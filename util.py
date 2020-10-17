import re
import os

def trim_margin(s:str, margin:str='|') -> str:
    pattern = r'^\s*' + re.escape(margin)
    string = s.strip()
    return re.sub(pattern, '', string, flags=re.M)


def mkdir_if_notexists(fp:str):
    dirname, _ = os.path.split(fp)
    if not os.path.exists(dirname):
        p_dirname, _ = os.path.split(dirname)
        if not os.path.exists(p_dirname):
            mkdir_if_notexists(dirname)
        os.mkdir(dirname)
