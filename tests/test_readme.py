import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.readme import (
	BALANCE_END_MARKER,
	BALANCE_START_MARKER,
	render_balance_table,
	update_readme_balances,
)

SAMPLE_BALANCES = [
	{'name': '主账号', 'provider': 'anyrouter', 'quota': 85.5, 'used': 14.5},
	{'name': '备用账号', 'provider': 'agentrouter', 'quota': 90.0, 'used': 10.0},
]


def test_render_balance_table_includes_totals():
	table = render_balance_table(SAMPLE_BALANCES)
	assert '主账号' in table
	assert '$85.50' in table
	# 总剩余 = 85.5 + 90 = 175.5
	assert '**$175.50**' in table
	# 总已用 = 14.5 + 10 = 24.5
	assert '**$24.50**' in table


def test_render_balance_table_escapes_pipe():
	table = render_balance_table([{'name': 'a|b', 'provider': 'p', 'quota': 1.0, 'used': 0.0}])
	assert 'a\\|b' in table


def _make_readme(tmp_path):
	content = f'# Demo\n\n{BALANCE_START_MARKER}\n> placeholder\n{BALANCE_END_MARKER}\n'
	readme = tmp_path / 'README.md'
	readme.write_text(content, encoding='utf-8')
	return readme


def test_update_writes_when_changed(tmp_path):
	readme = _make_readme(tmp_path)
	updated = update_readme_balances(SAMPLE_BALANCES, readme_path=str(readme), updated_at='2026-01-01')
	assert updated is True
	text = readme.read_text(encoding='utf-8')
	assert '主账号' in text
	assert '**$175.50**' in text
	assert BALANCE_START_MARKER in text
	assert BALANCE_END_MARKER in text


def test_update_skips_when_only_timestamp_differs(tmp_path):
	readme = _make_readme(tmp_path)
	update_readme_balances(SAMPLE_BALANCES, readme_path=str(readme), updated_at='2026-01-01')
	# 相同数据但不同时间戳，应跳过写入，保留原时间戳
	updated = update_readme_balances(SAMPLE_BALANCES, readme_path=str(readme), updated_at='2026-12-31')
	assert updated is False
	assert '2026-01-01' in readme.read_text(encoding='utf-8')


def test_update_writes_again_when_quota_changes(tmp_path):
	readme = _make_readme(tmp_path)
	update_readme_balances(SAMPLE_BALANCES, readme_path=str(readme), updated_at='2026-01-01')
	changed = [dict(SAMPLE_BALANCES[0], quota=80.0), SAMPLE_BALANCES[1]]
	updated = update_readme_balances(changed, readme_path=str(readme), updated_at='2026-01-02')
	assert updated is True
	assert '$80.00' in readme.read_text(encoding='utf-8')


def test_update_returns_false_without_markers(tmp_path):
	readme = tmp_path / 'README.md'
	readme.write_text('# No markers here\n', encoding='utf-8')
	updated = update_readme_balances(SAMPLE_BALANCES, readme_path=str(readme))
	assert updated is False


def test_update_returns_false_for_empty_balances(tmp_path):
	readme = _make_readme(tmp_path)
	updated = update_readme_balances([], readme_path=str(readme))
	assert updated is False
