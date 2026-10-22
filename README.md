# sqltk-store

**统一档案存储** · Library（不是 MCP）

> 所有 MCP 的**唯一数据落点**。零第三方依赖（标准库 `sqlite3`），任何 MCP 都能无负担依赖。
> `mcp-profile-hub` 是它的 MCP 外壳；但装不装 hub，不影响任何 MCP 写档案。

> 发行名 `sqltk-store`，import 包名 `dbstore`（`pip install sqltk-store` → `import dbstore`）—— 两者不同是刻意的，原因见顶层 README「命名」。

## 安装

```bash
pip install sqltk-store                        # 从 PyPI
pip install ./sqltk-store                      # 从源码（在工具链根目录执行）
```

## 为什么不通过 MCP 协议集中写

如果档案写入要绕一次 MCP 调用，就等于「没装 profile-hub 就丢数据」。
把存储做成**库**，让每个 MCP 直接写同一个 SQLite，才是真的「单一落点 + 按需安装」。

## 表结构（schema v3）

| 表 | 用途 |
|---|---|
| `instances` | 实例档案（方言/版本/库名/元数据） |
| `observations` | 观测原始事件（六种 kind + 结构化指标列） |
| `metric_windows` | 指标聚合档（5m / 1h / 1d） |
| `metric_baselines` | **分位数基线** p50/p95/p99 + spread（不是单值） |
| `sql_profiles` | 一条 SQL 的一生（首末次出现、次数） |
| `finding_lifecycle` | 技术债账本（open → confirmed → fixing → fixed → verified / dismissed） |
| `incidents` | 事故单（症状/诊断/时间线/关闭时间） |
| `suspect_links` | 变更 ↔ 异常的时间关联 |
| `changes` | 变更单与状态机轨迹 |
| `audit_log` | 审计流水 |
| `dictionary` | 口径/对象字典 |

## 关键约定

- `tier_of()` / `require_tier()`：一个实例的历史够不够谈趋势，由存储层统一裁决
- `compute_metric_baselines()`：样本 < 2 直接跳过，**绝不编造基线**
- `transition_finding()`：非法状态转移抛 `ValueError`，`verified` 是终态
- `export_profile()` / `import_profile()`：脱敏知识包，支持行业基线交换

## 存储位置

`$DBT_STORE`，默认 `~/.dbtoolchain/profile.db`。测试与多租户用环境变量隔开即可。

## 开发

```bash
python tests/test_dbstore.py
```

## 许可

MIT © 2026 罗文星 —— 见 [LICENSE](LICENSE)。
