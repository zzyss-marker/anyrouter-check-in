#!/usr/bin/env python3
"""
README 账号额度概览自动更新模块

在 README 中维护一段由标记包裹的区块，签到运行后写入每个账号的剩余额度、
已用额度以及总剩余。仅当表格数据发生变化时才写文件（忽略时间戳行），
避免每次运行都产生无意义的提交。
"""

from datetime import datetime, timedelta, timezone

BALANCE_START_MARKER = '<!-- BALANCE_START -->'
BALANCE_END_MARKER = '<!-- BALANCE_END -->'

# 北京时间 (UTC+8)，签到脚本面向中文用户，统一展示该时区
_BEIJING_TZ = timezone(timedelta(hours=8))


def _escape_cell(text) -> str:
	"""转义 Markdown 表格单元格中的特殊字符"""
	return str(text).replace('|', '\\|').replace('\n', ' ').strip()


def render_balance_table(account_balances: list[dict]) -> str:
	"""渲染账号额度 Markdown 表格（不含时间戳）

	Args:
		account_balances: 每个元素包含 name / provider / quota / used

	Returns:
		str: Markdown 表格字符串
	"""
	total_quota = sum(b.get('quota', 0) for b in account_balances)
	total_used = sum(b.get('used', 0) for b in account_balances)

	lines = [
		'| 账号 | 服务商 | 剩余额度 | 已用额度 |',
		'| :-- | :-- | --: | --: |',
	]
	for b in account_balances:
		name = _escape_cell(b.get('name', ''))
		provider = _escape_cell(b.get('provider', ''))
		quota = b.get('quota', 0)
		used = b.get('used', 0)
		lines.append(f'| {name} | {provider} | ${quota:.2f} | ${used:.2f} |')

	lines.append(f'| **总计** | — | **${total_quota:.2f}** | **${total_used:.2f}** |')
	return '\n'.join(lines)


def render_balance_section(account_balances: list[dict], updated_at: str) -> str:
	"""渲染完整的额度区块内容（时间戳 + 表格）"""
	table = render_balance_table(account_balances)
	return f'> 最后更新：{updated_at}\n\n{table}'


def _strip_timestamp(section: str) -> str:
	"""移除区块中的时间戳行，便于仅比较数据是否变化"""
	lines = [line for line in section.splitlines() if not line.strip().startswith('> 最后更新')]
	return '\n'.join(lines)


def _extract_section(content: str) -> str | None:
	"""提取标记之间的现有内容，标记缺失时返回 None"""
	start = content.find(BALANCE_START_MARKER)
	end = content.find(BALANCE_END_MARKER)
	if start == -1 or end == -1 or end < start:
		return None
	return content[start + len(BALANCE_START_MARKER) : end]


def update_readme_balances(
	account_balances: list[dict],
	*,
	readme_path: str = 'README.md',
	updated_at: str | None = None,
) -> bool:
	"""更新 README 中的账号额度概览区块。

	仅当额度表格内容发生变化时才写入文件（忽略时间戳行），
	以避免每次运行都产生无意义的提交。

	Args:
		account_balances: 每个元素包含 name / provider / quota / used
		readme_path: README 文件路径
		updated_at: 自定义更新时间字符串，默认使用当前北京时间

	Returns:
		bool: 是否实际更新了文件
	"""
	if not account_balances:
		return False

	try:
		with open(readme_path, 'r', encoding='utf-8', newline='') as f:
			content = f.read()
	except OSError as e:
		print(f'[WARN] Unable to read {readme_path}: {e}')
		return False

	old_section = _extract_section(content)
	if old_section is None:
		print(f'[WARN] Balance markers not found in {readme_path}, skip README update')
		return False

	new_table = render_balance_table(account_balances)

	# 比较时忽略时间戳行，仅在表格数据变化时才更新，避免无意义的提交
	if _strip_timestamp(old_section).strip() == new_table.strip():
		print('[INFO] README balances unchanged, skip writing')
		return False

	if updated_at is None:
		updated_at = datetime.now(_BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S (UTC+8)')

	new_section = f'\n{render_balance_section(account_balances, updated_at)}\n'
	start = content.find(BALANCE_START_MARKER) + len(BALANCE_START_MARKER)
	end = content.find(BALANCE_END_MARKER)
	new_content = content[:start] + new_section + content[end:]

	try:
		with open(readme_path, 'w', encoding='utf-8', newline='') as f:
			f.write(new_content)
	except OSError as e:
		print(f'[WARN] Unable to write {readme_path}: {e}')
		return False

	print(f'[INFO] README balance overview updated ({len(account_balances)} account(s))')
	return True
