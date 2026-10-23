"""Offline skill-content and HTML serialization checks, not exploit verification."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
main = (root / 'SKILL.md').read_text() if (root / 'SKILL.md').exists() else ''
ref = root / 'references/six-misconfigs.md'
text = ref.read_text() if ref.exists() else ''
checks = {'skill_exists': bool(main), 'reference_linked': 'references/six-misconfigs.md' in main, 'reference_exists': bool(text)}
for term in ['?_method=PUT', 'X-HTTP-Method-Override', 'CRLF', 'third-party', 'step-up', 'unverified', 'not a Spring default', 'attacker login']:
    checks[term] = term in text
checks['six_conditions'] = len(re.findall(r'^\d\. \*\*', text.split('## Browser reachability')[0], re.M)) == 6
checks['source_attribution'] = 'https://mian-hizb.netlify.app/writeups/csrf-to-account-takeover-six-misconfigs/' in text
checks['no_status_only_claim'] = bool(main) and 'If the server returns 200, you have CSRF.' not in main

class Form(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.forms = []

    def handle_starttag(self, tag, attrs):
        if tag == 'input': self.inputs.append(dict(attrs))
        if tag == 'form': self.forms.append(dict(attrs))

parser = Form()
blocks = re.findall(r'```html\n(.*?)```', text, re.S)
if blocks: parser.feed(blocks[0])
checks['one_control'] = len(parser.inputs) == 1
checks['form_post_plain'] = bool(parser.forms) and parser.forms[0].get('method') == 'POST' and parser.forms[0].get('enctype') == 'text/plain'
checks['form_bytes_json'] = False
if parser.inputs:
    entry = parser.inputs[0]
    body = (entry['name'] + '=' + entry.get('value', '') + '\r\n').encode()
    try:
        checks['form_bytes_json'] = json.loads(body) == {'email': 'researcher@example.test', 'padding': '='} and body.endswith(b'\r\n')
    except json.JSONDecodeError: pass
checks['frontmatter'] = main.startswith('---\n') and bool(re.search(r'^name: csrf-account-takeover-chain$', main, re.M))
checks['proof_gates'] = all(term in main for term in ['backend candidate', 'browser CSRF', 'takeover proven'])
failures = [name for name, passed in checks.items() if not passed]
print(json.dumps(checks, indent=2))
print(f'{len(checks)-len(failures)}/{len(checks)} checks passed')
sys.exit(bool(failures))
