from . import colors as C
import re

def find_custom_formatter(instrument):
    if instrument in ("isgri", "jemx"):
        print(f"{C.GRAY} selected custom formatter for instrument {instrument} {C.NC}")
        return custom_progress_formatter
    else:
        print(f"{C.GRAY} NO custom formatter for instrument {instrument} {C.NC}")

def custom_progress_formatter(L):
    nscw = len(set([l['scwid'] for l in L if re.match("[0-9]{12}\.00[0-9]", l['scwid'])]))
    ndone = len(set([l['node'] for l in L if l['message'] == 'main done']))
    nrestored = len(set([l['node'] for l in L if l['message'] == 'restored from cache']))
    nnodes = len(set([l['node'] for l in L]))
    return f"in {nscw} SCW so far; nodes ({nnodes}): {ndone} computed {nrestored} restored"
