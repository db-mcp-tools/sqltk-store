#!/usr/bin/env python3
"""dbt-store 回归测试：档案存储 schema v3

不依赖 pytest / 真实数据库。直接运行：

    python tests/test_dbstore.py
"""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "src"))
# 开发期：兄弟仓库用源码目录；正式使用请 pip install（见 README）
for _sib in ():
    _p = _HERE.parent.parent / _sib / "src"
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

os.environ.setdefault("DBT_LOG_LEVEL", "ERROR")
_TMPDIR = tempfile.mkdtemp(prefix="dbt-dbstore-")
os.environ.setdefault("DBT_STORE", os.path.join(_TMPDIR, "store.db"))


PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASSED.append(name)
    else:
        FAILED.append(f"{name}  << {detail[:300] if detail else ''}")


def section(title: str) -> None:
    print(f"\n── {title}")



import dbstore as PS
# 13.2 profile_store v3（用临时库）
_orig_store = os.environ.get("DBT_STORE")
os.environ["DBTSTORE"] = ""
import tempfile, sqlite3 as _sq3
_tmpdb = os.path.join(tempfile.mkdtemp(), "v3test.db")
os.environ["DBT_STORE"] = _tmpdb
_iid = "it:v3:model"
PS.upsert_instance(_iid, dialect="mysql", version="8.0")
for _i in range(40):
    PS.record_metric_sample(_iid, "qps", 100 + _i)
PS.record_observation(_iid, "snapshot", {"metrics": {"connections_used": 12}})
check("metric_series 读回 40 个样本", len(PS.metric_series(_iid, "qps")) == 40)
check("tier 判定正常", PS.tier_of(_iid) == "tier1")
PS.aggregate_windows(_iid, "1h")
_bl = PS.compute_metric_baselines(_iid, "1h", min_samples=10)
check("分位数基线已建立且带 spread", _bl.get("qps", {}).get("spread", 0) > 0)
_blq = PS.get_metric_baseline(_iid, "qps", "1h")
check("get_metric_baseline 返回 p50/p95", _blq is not None and _blq["p50"] > 0)
check("无基线指标返回 None（不猜）", PS.get_metric_baseline(_iid, "not_exists", "1h") is None)
for _ in range(3):
    PS.record_sql_seen("fp:model1", "SELECT * FROM t", "select")
check("SQL 档案累计出现次数", PS.get_sql_profile("fp:model1")["occurrence_count"] == 3)
_f = PS.record_finding(_iid, "SEL001", object_ref="t", fingerprint="fp:model1", severity="medium")
PS.record_finding(_iid, "SEL001", object_ref="t", fingerprint="fp:model1", severity="high")
_lc = PS.list_findings(_iid)
check("账本聚合同一发现且取更严重 severity",
      len(_lc) == 1 and _lc[0]["occurrences"] == 2 and _lc[0]["severity"] == "high")
PS.transition_finding(_f["finding_id"], "confirmed")
PS.transition_finding(_f["finding_id"], "fixing")
PS.transition_finding(_f["finding_id"], "fixed")
PS.transition_finding(_f["finding_id"], "verified")
try:
    PS.transition_finding(_f["finding_id"], "open")
    check("verified 是终态不许再转移", False)
except ValueError:
    check("verified 是终态不许再转移", True)
_st = PS.finding_stats(_iid)
check("finding_stats 口径正确", _st["done"] == 1 and _st["open"] == 0)
_inc = PS.open_incident(_iid, "测试事故")
PS.update_incident(_inc, diagnosis={"primary": "REPL001"}, timeline_event={"ev": "t"})
PS.close_incident(_inc)
_li = PS.list_incidents(_iid)
check("事故单闭环且有诊断与时间线",
      _li and _li[0]["closed_at_iso"] and _li[0]["diagnosis"].get("primary") == "REPL001"
      and _li[0]["timeline"])
PS.add_suspect_link("an:x", "chg:y", 42.0)
check("suspect_link 读写", PS.suspects_for("an:x")[0]["change_id"] == "chg:y")
if _orig_store is None:
    os.environ.pop("DBT_STORE", None)
else:
    os.environ["DBT_STORE"] = _orig_store


# ==================================================================
print("\n" + "=" * 60)
print("通过 %d 项，失败 %d 项" % (len(PASSED), len(FAILED)))
if FAILED:
    print("\n失败明细：")
    for _f in FAILED:
        print("  ✗", _f)
    raise SystemExit(1)
print("全部通过")
