import os
import sys
import re
import json
import shutil
import datetime
import subprocess
from typing import Optional, List, Dict, Any

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_FILE = os.path.join(MODULE_DIR, "knowledge_base.json")
LOG_FILE = os.path.join(MODULE_DIR, "evolution_log.json")
MCP_SCHEMA_DIRS = [
    os.path.expanduser("~/.gemini/antigravity-cli/mcp/sap-commerce-mcp"),
    os.path.expanduser("~/.gemini/antigravity/mcp/sap-commerce-mcp"),
    os.path.expanduser("~/.gemini/antigravity-cli/mcp/hybris-hac")
]

INITIAL_KNOWLEDGE = [
    {
        "id": "kb_lang_zh_cn",
        "pattern": "Language 'zh_CN' not found",
        "description": "Commerce Cloud standard Simplified Chinese language code in C2L table is 'zh', not 'zh_CN'.",
        "resolution": "Automatically normalize 'zh_CN' to 'zh' when generating ImpEx for Language and localized attributes.",
        "tags": ["i18n", "language", "impex"],
        "created_at": "2026-09-11T11:00:00"
    },
    {
        "id": "kb_b2b_budget_fields",
        "pattern": "B2BBudget creation failure",
        "description": "B2BBudget requires Unit(uid) and dateRange[dateformat=dd.MM.yyyy hh:mm:ss,allownull=true].",
        "resolution": "Always link B2BBudget to root B2BUnit and specify full dateRange.",
        "tags": ["b2b", "budget", "impex"],
        "created_at": "2026-09-11T11:00:00"
    },
    {
        "id": "kb_solr_cronjob_bypass",
        "pattern": "Solr reindex cannot be performed yet / cronjob queued",
        "description": "Triggering cronjobs can get delayed or blocked by scheduler state.",
        "resolution": "Call IndexerService.performFullIndex(cfg) directly in JVM via Groovy for immediate synchronous execution.",
        "tags": ["solr", "indexer", "groovy"],
        "created_at": "2026-09-11T11:00:00"
    },
    {
        "id": "kb_hsqldb_polymorphic_query",
        "pattern": "HSQLDB column type cast exception with OAuthClientDetails / AbstractPage",
        "description": "FlexibleSearch with polymorphic sub-types can fail on direct attribute selects.",
        "resolution": "Query SELECT {pk} and fetch required attributes via Java/Groovy getters.",
        "tags": ["flexsearch", "hsqldb", "groovy"],
        "created_at": "2026-09-11T11:00:00"
    },
    {
        "id": "kb_b2b_cost_center_type",
        "pattern": "Type code invalid for CostCenter",
        "description": "In Hybris B2B commerce, the ItemType is B2BCostCenter, not CostCenter.",
        "resolution": "Query and import using type code B2BCostCenter.",
        "tags": ["b2b", "costcenter", "impex"],
        "created_at": "2026-09-11T11:00:00"
    }
]

class SelfImprover:
    def __init__(self, module_dir: str = MODULE_DIR):
        self.module_dir = module_dir
        self.kb_file = KB_FILE
        self.log_file = LOG_FILE
        self._ensure_kb()

    def _ensure_kb(self):
        if not os.path.exists(self.kb_file):
            with open(self.kb_file, "w", encoding="utf-8") as f:
                json.dump(INITIAL_KNOWLEDGE, f, ensure_ascii=False, indent=2)
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load_kb(self) -> List[Dict[str, Any]]:
        try:
            with open(self.kb_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return INITIAL_KNOWLEDGE

    def _save_kb(self, data: List[Dict[str, Any]]):
        with open(self.kb_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_logs(self) -> List[Dict[str, Any]]:
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_logs(self, data: List[Dict[str, Any]]):
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def record_learning(
        self,
        pattern_name: str,
        problem: str,
        solution: str,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Records a new learned experience, error pattern, or best practice into the knowledge base.
        """
        now = datetime.datetime.now().isoformat()
        slug = re.sub(r'[^a-zA-Z0-9_]', '_', pattern_name.lower()).strip('_')
        entry = {
            "id": f"kb_{slug}_{int(datetime.datetime.now().timestamp())}",
            "pattern": pattern_name,
            "description": problem,
            "resolution": solution,
            "tags": tags or ["learned"],
            "created_at": now
        }

        kb = self._load_kb()
        kb.insert(0, entry)
        self._save_kb(kb)
        return f"💡 [自完善经验库] 成功录入经验条目: '{pattern_name}' (ID: {entry['id']})"

    def query_kb(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches the knowledge base for known patterns and resolutions.
        """
        kb = self._load_kb()
        q_lower = query.lower()
        results = []
        for item in kb:
            searchable = f"{item['pattern']} {item['description']} {item['resolution']} {' '.join(item.get('tags', []))}".lower()
            if q_lower in searchable:
                results.append(item)
        return results

    def refresh_mcp_schemas(self) -> str:
        """
        Refreshes all MCP JSON schemas in antigravity directory.
        """
        python_bin = os.path.join(self.module_dir, "venv", "bin", "python")
        server_py = os.path.join(self.module_dir, "server.py")
        p = subprocess.Popen(
            [python_bin, server_py],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        msg_init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "refresher", "version": "1.0"}}}
        p.stdin.write(json.dumps(msg_init) + "\n")
        p.stdin.flush()
        p.stdout.readline()

        p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        p.stdin.flush()

        msg_list = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        p.stdin.write(json.dumps(msg_list) + "\n")
        p.stdin.flush()
        line = p.stdout.readline()
        tools = json.loads(line).get("result", {}).get("tools", [])

        count = 0
        for target_dir in MCP_SCHEMA_DIRS:
            os.makedirs(target_dir, exist_ok=True)
            for t in tools:
                schema_path = os.path.join(target_dir, f"{t['name']}.json")
                tool_data = {
                    "name": t.get("name"),
                    "description": t.get("description"),
                    "parameters": t.get("inputSchema", {})
                }
                with open(schema_path, "w", encoding="utf-8") as f:
                    json.dump(tool_data, f, ensure_ascii=False, indent=2)
            count = len(tools)

        p.terminate()
        return f"✅ 已自动刷新并同步全部 {count} 个 MCP 工具 Schema 至 {MCP_SCHEMA_DIRS[0]}"

    def apply_improvement(
        self,
        target_file: str,
        improvement_description: str,
        new_file_content: str
    ) -> str:
        """
        Applies a hot-improvement or fix to an MCP module with automatic backup and test verification.
        """
        full_target = os.path.join(self.module_dir, target_file) if not os.path.isabs(target_file) else target_file
        if not os.path.exists(full_target):
            return f"❌ Target file '{full_target}' does not exist."

        backup_file = f"{full_target}.bak"
        shutil.copy2(full_target, backup_file)

        # 1. Apply new content
        try:
            with open(full_target, "w", encoding="utf-8") as f:
                f.write(new_file_content)
        except Exception as e:
            shutil.copy2(backup_file, full_target)
            return f"❌ Failed to write update to {full_target}: {e}"

        # 2. Python syntax compile check
        python_bin = os.path.join(self.module_dir, "venv", "bin", "python")
        compile_res = subprocess.run([python_bin, "-m", "py_compile", full_target], capture_output=True, text=True)
        if compile_res.returncode != 0:
            shutil.copy2(backup_file, full_target)
            return f"❌ Syntax check failed! Reverted changes. Error:\n{compile_res.stderr}"

        # 3. Regression test run
        test_py = os.path.join(self.module_dir, "test_server.py")
        test_res = subprocess.run([python_bin, test_py], capture_output=True, text=True)
        if test_res.returncode != 0:
            shutil.copy2(backup_file, full_target)
            return f"❌ Regression tests failed! Reverted changes. Test Output:\n{test_res.stdout}\n{test_res.stderr}"

        # 4. Remove backup, record evolution log
        os.remove(backup_file)
        now = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": now,
            "target_file": os.path.basename(full_target),
            "description": improvement_description,
            "status": "VERIFIED_AND_APPLIED"
        }
        logs = self._load_logs()
        logs.insert(0, log_entry)
        self._save_logs(logs)

        # 5. Refresh MCP schemas
        schema_status = self.refresh_mcp_schemas()

        return f"🚀 **MCP 自完善更新成功且验证通过！**\n- **改进文件:** `{os.path.basename(full_target)}`\n- **改进说明:** {improvement_description}\n- **回归测试:** 100% 通过\n- **Schema 同步:** {schema_status}"

    def diagnose_self(self) -> str:
        """
        Audits MCP health, script library count, learned knowledge base rules, and internal components.
        """
        modules_status = []
        modules_to_check = [
            ("HAC 核心通讯", "hac_client"),
            ("B2B 组织层级", "b2b_org_helper"),
            ("Spartacus 医生", "spartacus_doctor"),
            ("绿色站点编排", "site_scaffolder"),
            ("外部站点爬虫", "storefront_crawler"),
            ("Solr 索引同步", "solr_sync_helper"),
            ("脚本资产库", "script_manager"),
            ("自完善自进化引擎", "self_improver"),
            ("Drools 促销引擎", "promotion_helper"),
            ("Composable Storefront 编排", "storefront_helper"),
        ]
        
        all_ok = True
        for name, mod_name in modules_to_check:
            try:
                __import__(mod_name)
                modules_status.append(f"  • {name} (`{mod_name}`): 🟢 正常就绪")
            except Exception as e:
                all_ok = False
                modules_status.append(f"  • {name} (`{mod_name}`): 🔴 异常 ({e})")

        kb = self._load_kb()
        logs = self._load_logs()

        # Count scripts in library
        lib_index_file = os.path.join(self.module_dir, "script_library", "index.json")
        lib_count = 0
        if os.path.exists(lib_index_file):
            try:
                with open(lib_index_file, "r", encoding="utf-8") as f:
                    lib_count = len(json.load(f))
            except Exception:
                pass

        out = [
            "🛠️ **=== SAP-Commerce-MCP 自我健康与自进化状态审计 ===**",
            f"- **运行健康状态:** {'🟢 核心模块全部正常就绪' if all_ok else '🔴 部分模块异常'}",
            f"- **沉淀成功脚本数:** `{lib_count}` 个已验证脚本（保存在 `script_library/`）",
            f"- **沉淀经验知识库:** `{len(kb)}` 条避坑规则（保存在 `knowledge_base.json`）",
            f"- **历史自完善更新:** `{len(logs)}` 次经测试验证的代码热更新",
            "\n🧩 **模块就绪明细:**",
            "\n".join(modules_status),
        ]
        if logs:
            out.append("\n📋 **最近自完善记录:**")
            for l in logs[:3]:
                out.append(f"  • [{l['timestamp'][:16]}] {l['target_file']}: {l['description']}")

        if kb:
            out.append("\n💡 **核心避坑规则样例:**")
            for k in kb[:3]:
                out.append(f"  • **{k['pattern']}**: {k['resolution']}")

        return "\n".join(out)
