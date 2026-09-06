"""Exercise the real local agent; isolate checkpoints, preserve production tasks."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import sys
import runpy
import re

if '--verify' in sys.argv:
    evidence = Path(sys.argv[sys.argv.index('--verify') + 1])
    results = json.loads((evidence / 'results.json').read_text())
    assert len(results) == 5, 'Five completed task results are required'
    assert [item['task'] for item in results] == [1, 2, 3, 4, 5], 'Each distinct task must finish once'
    assert all(item['answer'].strip() and not any(marker in item['answer'] for marker in
               ('[INCOMPLETE]', '[BLOCKED:', '[ERROR:')) for item in results), 'Unfinished answers cannot pass'
    assert re.search(r'(?<!\d)4,?201(?!\d)', results[0]['answer'])
    totals = json.loads((evidence / 'totals.json').read_text())
    # The request specifies the data, not JSON key names.
    assert any(value == {'pear': 5, 'apple': 5} for value in totals.values())
    assert any(isinstance(value, (int, float)) and not isinstance(value, bool)
               and value == 10 for value in totals.values())
    for block in re.findall(r'```json\s*\n(.*?)```', results[1]['answer'], re.S | re.I):
        assert json.loads(block) == totals, 'The final answer must match the actual JSON artifact'
    unique = runpy.run_path(str(evidence / 'dedupe.py'))['unique_in_order']
    for values, expected in [([], []), ([9, 2, 9, 1], [9, 2, 1]),
                             (['z', 'a', 'z'], ['z', 'a']),
                             ([[2], [1], [2]], [[2], [1]]),
                             ([{'a': 1}, {'a': 1}, {'b': 2}], [{'a': 1}, {'b': 2}]),
                             ([{1}, frozenset({1})], [{1}]),
                             ([frozenset({1}), {1}], [frozenset({1})])]:
        assert unique(values) == expected, values
    print('ARITHMETIC_CSV_CODE_FOLLOWUP_INDEPENDENTLY_VERIFIED')
    print('Windows response requires comparison against independent live CIM evidence:')
    print(results[4]['answer'])
    raise SystemExit(0)

loader = importlib.machinery.SourceFileLoader('nature_live', os.environ.get('NATURE_AGENT_SOURCE', '/root/.local/bin/llama-agent'))
spec = importlib.util.spec_from_loader(loader.name, loader)
nature = importlib.util.module_from_spec(spec)
loader.exec_module(nature)
continuing = '--continue' in sys.argv
root = (Path(sys.argv[sys.argv.index('--continue') + 1]).resolve() if continuing
        else Path(tempfile.mkdtemp(prefix='nature-general-')))
assert root.parent == Path('/tmp') and root.name.startswith('nature-general-')
for name in ('ACTIVE_TASK_FILE', 'ACTIVE_TASK_LEASE_FILE', 'TASK_HISTORY_DIR',
             'EVENT_LOG_FILE', 'SOURCE_LOG_FILE'):
    setattr(nature, name, root / Path(getattr(nature, name)).name)
nature.TASK_HISTORY_DIR.mkdir(exist_ok=True)
os.chdir(root)
if '--conversation-regression' in sys.argv:
    narration = nature.narrate({'type': 'command', 'cmd': 'cd /tmp/project && worker & echo "started pid $!"'})
    assert '/tmp/project' in narration and 'started pid' not in narration
    partial_ranking = nature.deterministic_largest_files_answer(
        'F:\\file.bin|12|0.000 GB\nSUMMARY|files|ranked=1|errors=2|skipped_links=3', 'F', 100)
    assert 'Coverage limits: 2 unreadable' in partial_ranking and '3 reparse' in partial_ranking
    objective = 'Use live Windows system information to report its version.'
    transition = [{'role': 'system', 'content': 'Answer the current request.'}]
    transition += [{'role': 'assistant', 'content': f'Previous coding evidence {index}'} for index in range(25)]
    transition.append({'role': 'user', 'content': objective})
    compacted = nature.trim_conversation(transition, nature.TaskState(objective))
    assert any(m.get('role') == 'user' and m.get('content') == objective for m in compacted), 'Compaction must retain the new user request, not only a system summary'
    live_state = nature.TaskState(objective)
    assert any('live evidence' in gap for gap in live_state.completion_gaps('Old task answer. [TASK_COMPLETE]'))
    live_state.observe_tool({'type': 'command', 'cmd': 'system-query'}, 'fresh system evidence')
    assert not any('live evidence' in gap for gap in live_state.completion_gaps('Result. [TASK_COMPLETE]'))
    for body in ('(Get-CimInstance Win32_OperatingSystem).Caption; Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum',
                 '1,2,3 | Measure-Object -Sum'):
        command = f'{nature.WINDOWS_POWERSHELL} -NoProfile -Command "{body}"'
        assert nature.intercept_command(command, 'Report live Windows version and RAM.') == nature.normalize_direct_windows_powershell(command)
    import shlex
    body = "$os = Get-CimInstance Win32_OperatingSystem; Write-Output $os.Caption"
    normalized = nature.normalize_direct_windows_powershell(f'{nature.WINDOWS_POWERSHELL} -Command "{body}"')
    assert shlex.split(normalized)[-1] == body
    assert shlex.quote(body) in normalized, 'Bash must not expand PowerShell variables'
    assert 'run_python' in {t['function']['name'] for t in nature.select_tools('Create dedupe.py and test it.')}
    (root / 'local_import_fixture.py').write_text('VALUE = 37\n')
    imported = nature.execute_tool_call({'type': 'python', 'code':
        'from local_import_fixture import VALUE\nassert VALUE == 37\nprint("PROJECT_IMPORT_OK")'})
    assert 'PROJECT_IMPORT_OK' in imported and '[EXIT CODE:' not in imported, imported
    nature.ensure_model_server_until_ready = lambda *a, **kw: True
    nature.send_message = lambda *a, **kw: {'content': 'A triangle has three sides. [TASK_COMPLETE]', 'finish_reason': 'stop'}
    history = [{'role': 'system', 'content': 'Answer accurately.'}]
    answer = nature._agent_turn_active('Explain a triangle briefly.', history)
    assert history[-1] == {'role': 'assistant', 'content': answer}, history
    assert nature._is_verification_call({'type': 'python', 'code': 'assert 2 + 2 == 4'})
    assert not nature._is_verification_call({'type': 'python', 'code': 'print("verified")'})
    assert not nature._is_verification_call({'type': 'python', 'code': 'open("x", "w").write("x"); assert True'})
    assert nature._is_verification_call({'type': 'command', 'cmd':
        "cd /tmp/project && python3 -c 'assert 2 + 2 == 4'"})
    assert not nature._is_verification_call({'type': 'command', 'cmd':
        "python3 -c 'print(\"verified\")'"})
    assert not nature._is_verification_call({'type': 'command', 'cmd':
        "echo python3 -c 'assert 2 + 2 == 4'"})
    import io
    class Reporter:
        calls = 0
        def report(self, elapsed):
            return ('sample', 'measured operation')
        def english_report(self):
            self.calls += 1
            return 'Generated 7 additional tokens.'
    reporter = Reporter()
    stream = io.StringIO()
    live = nature.LiveProgress(stream=stream, interactive=False)
    live._reporter = reporter.report
    live.refresh(force=True)
    live._last_english_at = time.monotonic() - 2
    live.refresh()
    assert reporter.calls == 0, 'Do not consume deltas before they can be printed'
    live._last_logged_at = time.monotonic() - 2
    live._last_visible_at = time.monotonic() - 2
    live.refresh()
    assert 'Generated 7 additional tokens.' in stream.getvalue()
    partial = {'type': 'python', 'code': "from pathlib import Path\nPath('partial.txt').write_text('expected')\nassert False, 'intentional check failure'"}
    output = nature.execute_tool_call(partial, 'Create partial.txt and verify its content.')
    state = nature.TaskState('Create partial.txt and verify its content.')
    success, _ = state.observe_tool(partial, output)
    assert not success
    assert state.mutations == 1 and state.pending_reconciliation, 'Retain actual writes despite a later failure'
    check = {'type': 'read', 'path': str(root / 'partial.txt')}
    state.observe_tool(check, nature.execute_tool_call(check))
    assert state.pending_reconciliation is None
    assert state.last_verification_sequence > state.last_mutation_sequence
    artifact = root / 'report.json'
    artifact.write_text('{"count": 7}')
    objective = f'Save the report to {artifact}'
    assert nature.json_artifact_response_gaps(objective, 'report.json contains:\n```json\n{"count": 8}\n```')
    assert not nature.json_artifact_response_gaps(objective, 'report.json contains:\n```json\n{"count": 7}\n```')
    spaced = root / 'space dir' / 'report.json'
    spaced.parent.mkdir()
    spaced.write_text('{"count": 9}')
    assert not nature.json_artifact_response_gaps(f'Save "{spaced}"', 'report.json contains:\n```json\n{"count": 9}\n```')
    strategy = nature.TaskState('Update an existing module.')
    strategy.observe_tool({'type': 'patch', 'patch': 'first invalid patch'}, '[ERROR: validation failed]')
    assert not strategy.patch_strategy_failed()
    strategy.observe_tool({'type': 'read', 'path': 'module.py'}, 'current source')
    strategy.observe_tool({'type': 'patch', 'patch': 'different invalid patch'}, '[ERROR: another validation failure]')
    assert strategy.patch_strategy_failed(), 'Different failing patch text must still change the editing strategy'
    strategy.observe_tool({'type': 'write', 'path': 'module.py'}, '[File written]')
    assert not strategy.patch_strategy_failed(), 'Fresh changes invalidate the previous failure epoch'
    strategy.previous_objective = 'Create /tmp/example.py implementing a function.'
    restored = nature.TaskState('Update that function.', restored=strategy.to_dict())
    assert '/tmp/example.py' in restored.context_summary()
    resumed = nature.sanitize_resume_conversation([], 'Update that function.', strategy.previous_objective)
    assert '/tmp/example.py' in resumed[1]['content']
    print('CONVERSATION_CONTINUITY_OK')
    raise SystemExit(0)
os.chdir(root)
if not continuing:
    (root / 'sales.csv').write_text('item,quantity,price\npear,3,1.25\napple,2,2.50\npear,1,1.25\n')
prompts = [
    'Calculate (173 * 29) - (48 * 17). Give the exact integer.',
    f'Read {root}/sales.csv and calculate total revenue per item and overall. Save the totals as JSON in {root}/totals.json and verify them.',
    f'Create {root}/dedupe.py implementing unique_in_order(values), preserving the first occurrence of each value. Run tests for empty input, repeated integers, and repeated strings. Report the actual test results.',
    f'Update that Python function to also support unhashable values such as lists. Preserve its earlier behavior and run tests for both lists and integers.',
    'Use live Windows system information to report the Windows version, total physical RAM in GiB, and the name of each GPU. Do not guess.',
]
if '--ranking' in sys.argv:
    prompts = ['list top 100 heaviest files all over f drive']
nature.ensure_initial_server_until_ready(nature.find_model())
conversation = [{'role': 'system', 'content': nature.build_system_prompt()}]
print('LIVE_EVIDENCE_DIR=' + str(root), flush=True)
results = json.loads((root / 'results.json').read_text()) if continuing else []
pending = nature.load_pending_task() if continuing else None
if continuing:
    assert pending, 'Continuation requires the unfinished checkpoint'
    if results and '[INCOMPLETE]' in results[-1]['answer']:
        failed = results.pop()
        with (root / 'failed-attempts.jsonl').open('a') as attempts:
            attempts.write(json.dumps(failed) + '\n')
        (root / 'results.json').write_text(json.dumps(results, indent=2))
    conversation = nature.sanitize_resume_conversation(pending.get('conversation', []), pending['objective'], pending.get('previous_objective', ''))
for index, prompt in enumerate(prompts, 1):
    if '--task' in sys.argv and index != int(sys.argv[sys.argv.index('--task') + 1]):
        continue
    if index <= len(results):
        continue
    if pending:
        assert pending['objective'] == prompt, 'Never resume an unrelated objective'
    print(f'LIVE_TASK_START {index}: {prompt}', flush=True)
    started = time.monotonic()
    resumed = bool(pending)
    original_started = started
    if pending:
        for line in (root / 'events.jsonl').read_text().splitlines():
            event = json.loads(line)
            if event.get('kind') == 'start' and event.get('task_id') == pending['task_id']:
                original_started = event['monotonic_ms'] / 1000
                break
    answer = nature.agent_turn(prompt, conversation, resume_payload=pending)
    pending = None
    if nature.load_pending_task():
        raise RuntimeError('The task remains unfinished; its checkpoint is preserved')
    result = dict(task=index, prompt=prompt, seconds=time.monotonic()-original_started,
                  current_run_seconds=time.monotonic()-started, resumed=resumed, answer=str(answer))
    results.append(result)
    (root / 'results.json').write_text(json.dumps(results, indent=2))
    print('LIVE_TASK_RESULT ' + json.dumps(result), flush=True)
print('LIVE_TASKS_FINISHED', flush=True)
