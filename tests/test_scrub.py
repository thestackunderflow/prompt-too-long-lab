"""lab/scrub.py: Claude Code run logs are published, so host paths become <lab>/<home>, and account emails,
organization ids and API keys are removed. Measured numbers are never touched."""
import json, os, glob
from lab import scrub

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_windows_lab_path_json_escaped():
    raw = json.dumps({"cwd": "C:\\Users\\someone\\work\\prompt-too-long-lab\\evidence"})
    assert scrub.scrub_text(raw) == json.dumps({"cwd": "<lab>\\evidence"})


def test_posix_and_msys_lab_paths():
    assert scrub.scrub_text("mount C:/Users/someone/x/prompt-too-long-lab/claude-run") == "mount <lab>/claude-run"
    assert scrub.scrub_text("cd /c/Users/someone/x/prompt-too-long-lab/tests") == "cd <lab>/tests"
    assert scrub.scrub_text("/home/someone/src/prompt-too-long-lab/run.sh") == "<lab>/run.sh"


def test_home_folders_outside_the_lab():
    assert scrub.scrub_text("C:\\Users\\someone\\.claude\\x") == "<home>\\.claude\\x"
    assert scrub.scrub_text("/Users/someone/.claude/x") == "<home>/.claude/x"
    assert scrub.scrub_text("/home/someone/.claude") == "<home>/.claude"


def test_container_paths_are_kept():
    for s in ("/work/CLAUDE.md", "/root/.claude/projects/-work/memory/", "/usr/local/lib/python3.12/argparse.py"):
        assert scrub.scrub_text(s) == s


def test_keys_and_account_fields_removed():
    line = json.dumps({"apiKey": "sk-ant-api03-AbCdEf0123456789xyz", "email": "a.person@example.com",
                       "organization_id": "0f0e-1234", "accountUuid": "abcd", "input_tokens": 198179})
    out = json.loads(scrub.scrub_text(line))
    assert "sk-ant" not in json.dumps(out)
    assert out["email"] == "<redacted>" and out["organization_id"] == "<redacted>" and out["accountUuid"] == "<redacted>"
    assert out["input_tokens"] == 198179


def test_numbers_and_request_ids_unchanged():
    s = '{"total_cost_usd":0.3151,"request_id":"req_011CgBYe6KFYSQtqPz4cFESf","pre_tokens":105857}'
    assert scrub.scrub_text(s) == s


def test_committed_evidence_is_already_clean():
    files = [f for f in glob.glob(os.path.join(HERE, 'evidence', '**', '*'), recursive=True) if os.path.isfile(f)]
    assert files
    for f in files:
        t = open(f, encoding='utf8').read()
        assert scrub.scrub_text(t) == t, f
