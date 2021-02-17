from . import colors as C
import re

import logging

logger = logging.getLogger(__name__)

def find_custom_formatter(instrument):
    if instrument in ("isgri", "jemx"):
        logger.debug(f"{C.GRAY} selected custom formatter for instrument {instrument} {C.NC}")
        return custom_progress_formatter
    else:
        logger.debug(f"{C.GRAY} NO custom formatter for instrument {instrument} {C.NC}")

def custom_progress_formatter(L):
    nscw = len(set([l.get('scwid', 'none') for l in L if re.match("[0-9]{12}\.00[0-9]", l.get('scwid', 'none'))]))
    ndone = len(set([l.get('node', 'none') for l in L if l.get('message', 'none') == 'main done']))
    nrestored = len(set([l.get('node', 'none') for l in L if l['message'] == 'restored from cache']))
    nnodes = len(set([l.get('node', 'none') for l in L]))
    return f"in {nscw} SCW so far; nodes ({nnodes}): {ndone} computed {nrestored} restored"
