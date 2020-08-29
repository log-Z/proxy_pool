import re

def trim_margin(s:str, margin:str='|') -> str:
    pattern = r'^\s*' + re.escape(margin)
    string = s.strip()
    return re.sub(pattern, '', string, flags=re.M)
