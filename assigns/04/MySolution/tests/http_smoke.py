"""Live HTTP checks against a running workbench (default http://127.0.0.1:8040)."""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8040'


def req(path, data=None):
    body = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(
        BASE + path,
        data=body,
        headers={'Content-Type': 'application/json'} if body else {},
        method='GET' if body is None else 'POST',
    )
    try:
        with urllib.request.urlopen(request) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode())


checks = []


def check(ok, msg):
    checks.append((bool(ok), msg))
    print(('PASS' if ok else 'FAIL'), msg)


code, state = req('/api/state')
check(code == 200 and state['revision'] == 0 and not state['busy'], 'F4: idle without applied source')

code, examples = req('/api/examples')
check(code == 200 and {'Factorial', 'Fibonacci', 'Arithmetic', 'Undeclared', 'Runtime-error'} <= set(examples), 'F1: examples menu data')

code, state = req('/api/source', {'source': examples['Factorial'], 'name': 'Factorial.lambda'})
check(code == 200 and state['revision'] == 1 and state['name'] == 'Factorial.lambda', 'F1/F8: load factorial revision 1')
code, state = req('/api/action', {'operation': 'interpret'})
check(code == 200 and state['results'][-1]['text'] == 'D0Vint(arg1=120)' and state['results'][-1]['outcome'] == 'success', 'F6: factorial=120')

code, state = req('/api/source', {'source': examples['Fibonacci'], 'name': 'Fibonacci.lambda'})
check(state['revision'] == 2 and state['results'] == [], 'F8: replacement clears results')
code, state = req('/api/action', {'operation': 'interpret'})
check(state['results'][-1]['text'] == 'D0Vint(arg1=55)', 'F6: fibonacci=55')

code, state = req('/api/source', {'source': 'D0Evar("x")', 'name': 'Untitled'})
code, state = req('/api/action', {'operation': 'lint'})
check(state['results'][-1]['outcome'] == 'language_error' and 'x' in state['results'][-1]['text'], 'F5: undeclared x')
code, state = req('/api/source', {'source': 'D0Elam("x", D0Evar("x"))', 'name': 'Untitled'})
code, state = req('/api/action', {'operation': 'lint'})
check(state['results'][-1]['outcome'] == 'success' and 'No free variables' in state['results'][-1]['text'], 'F5: closed lambda')

code, state = req('/api/source', {'source': examples['Runtime-error'], 'name': 'Runtime-error.lambda'})
code, state = req('/api/action', {'operation': 'lint'})
check(state['results'][-1]['outcome'] == 'success', 'F5/F6: lint passes on div0')
code, state = req('/api/action', {'operation': 'interpret'})
check(state['results'][-1]['outcome'] == 'runtime_error', 'F6: interpret runtime failure')

code, state = req('/api/action', {'operation': 'typecheck'})
check(state['results'][-1]['outcome'] == 'not_implemented', 'F7: typecheck placeholder')
code, state = req('/api/action', {'operation': 'compile'})
check(state['results'][-1]['outcome'] == 'not_implemented' and state['artifact'] is None, 'F7: compile placeholder')
code, body = req('/api/action', {'operation': 'execute'})
check(code == 400 and 'generated artifact' in body['error'], 'F4/F7: execute rejected')

prev, rev = state['source'], state['revision']
code, body = req('/api/source', {'source': '   ', 'name': 'Bad'})
check(code == 400, 'F3: reject whitespace')
code, state = req('/api/state')
check(state['source'] == prev and state['revision'] == rev, 'F3/F8: applied source preserved after rejection')
code, body = req('/api/source', {'source': 'x' * 65537, 'name': 'Big'})
check(code == 400 and '65,536' in body['error'], 'F3: reject oversize')

code, state = req('/api/source', {'source': 'D0Evar("<img src=x>")', 'name': 'xss'})
code, state = req('/api/action', {'operation': 'lint'})
check('<img' in state['results'][-1]['text'], 'F9: HTML-like names preserved in result text')

html = urllib.request.urlopen(BASE + '/').read().decode()
order = [html.find(f'data-action="{action}"') for action in ['lint', 'interpret', 'typecheck', 'compile', 'execute']]
check(all(i > 0 for i in order) and order == sorted(order), 'F4: button order in HTML')
check('disabled' in html.split('data-action="execute"')[1][:80], 'F4: execute disabled in markup')

js = urllib.request.urlopen(BASE + '/app.js').read().decode()
check('fetch(path' in js and 'localApi' in js, 'View uses HTTP fetch with offline fallback')

failed = [msg for ok, msg in checks if not ok]
print(f'\n{len(checks) - len(failed)}/{len(checks)} checks passed')
if failed:
    raise SystemExit('Failed: ' + '; '.join(failed))
print('HTTP integration OK')
