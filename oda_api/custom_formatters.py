def find_custom_formatter(instrument):
    if instrument in ("isgri", "jemx"):
        return custom_progress_formatter

def custom_progress_formatter(L):
    nscw = len(set([l['scwid'] for l in L]))
    ndone = len(set([l['node'] for l in L if l['message'] == 'main done']))
    nnodes = len(set([l['node'] for l in L]))
    return f"in {nscw} SCW so far, {nnodes} nodes, {ndone} computed"
