"""Model fingerprint shared by the result set, the consistency report and the browser worker:
sha256( sha256hex(model.py) + "\\n" + sha256hex(params.py) + "\\n" + sha256hex(inputs.json) ), hex.
assets/worker.js computes the same value from the bytes it actually loads.
Run: python3 -I scripts/fingerprint.py [model_dir]   (default model/abm)"""
import hashlib, sys
from pathlib import Path


def fingerprint(d):
    d = Path(d)
    h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return hashlib.sha256('\n'.join([h(d / 'model.py'), h(d / 'params.py'), h(d / 'inputs.json')]).encode()).hexdigest()


if __name__ == '__main__':
    print(fingerprint(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'model/abm'))
