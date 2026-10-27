"""CPython side: write tests/out-cpython.json."""
import json, sys, platform
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'model/abm'), str(HERE)]
import numpy  # noqa: E402
from cases import run_all  # noqa: E402
inputs = json.load(open(HERE.parent / 'model/abm/inputs.json'))
res = run_all(inputs)
json.dump({'runtime': f'CPython {platform.python_version()} numpy {numpy.__version__}', 'results': res},
          open(HERE / 'out-cpython.json', 'w'))
print('cpython cases:', len(res))
