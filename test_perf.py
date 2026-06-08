import time
import re

def _fast_boundary_match(terms, text: str) -> bool:
    safe_text = f" {text.replace('.', ' ').replace('/', ' ').replace('-', ' ')} "
    for t in terms:
        if f" {t.replace('.', ' ').replace('/', ' ').replace('-', ' ')} " in safe_text:
            return True
    return False

def _has_boundary_match_re(terms, text: str) -> bool:
    for t in terms:
        if re.search(r'\b' + re.escape(t) + r'\b', text):
            return True
    return False

text = "senior html engineer" * 100
terms = ["ai", "ml", "data", "platform", "software", "tech"]

start = time.perf_counter()
for _ in range(100000):
    _fast_boundary_match(terms, text)
print("String replace:", time.perf_counter() - start)

compiled_re = re.compile(r'\b(?:' + '|'.join(map(re.escape, terms)) + r')\b')
start = time.perf_counter()
for _ in range(100000):
    compiled_re.search(text)
print("Compiled RE:", time.perf_counter() - start)
