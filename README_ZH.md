# SAP Commerce Cloud MCP 服务器 (`SAP-Commerce-MCP`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![SAP Commerce Cloud](https://img.shields.io/badge/SAP%20Commerce%20Cloud-2211%20%7C%20CCv2-008FD3.svg)](https://help.sap.com/docs/SAP_COMMERCE_CLOUD)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md) | [中文说明](README_ZH.md)

**SAP-Commerce-MCP** (`sap-commerce-mcp`) 是专为 **SAP Commerce Cloud (Hybris)** 与 **Headless Composable Storefront (Spartacus)** 打造的企业级 Model Context Protocol (MCP) 服务端。它赋予 AI 助手（Claude、Antigravity、Cursor 等）直接操控、运维、编排与自愈 Commerce 系统的全套原生能力。

> 💡 **项目沿革（从 `hybris-hac-mcp` 到 `SAP-Commerce-MCP`）**：  
> 本项目最初作为内部轻量级 HAC 管理控制台调用桥梁（原名 `hybris-hac-mcp`）诞生，用于免除频繁手动登录 HAC 执行脚本。在经历**某世界 500 强快消饮料企业 eB2B 数字化改造**与**某全球医疗器械企业 B2B 审批流治理**等大型企业级真实战役后，全面进化为覆盖 **Greenfield 建站、B2B 组织与审批链体检、Drools 促销自动化编排、Spartacus 无头前台深度自愈、Solr 检索引擎运维及实战经验自沉淀** 的 Commerce 全生命周期 AI 架构师副驾驶。  
> *(注：为了对存量 Prompt、自动化脚本与已发布 Agent 保持 100% 向下兼容，工具名统一保持 `hac_*` 前缀。)*

---

## 🚀 极速安装与接入（10 秒搞定）

得益于对现代 Python MCP 标准（`pyproject.toml`）的原生支持，您**无需手动克隆仓库，无需手动创建虚拟环境，无需查找 Python 物理路径**！

### 方式 A（最推荐：`uvx` 免安装，直接运行）

只需将以下配置写入您的客户端配置文件即可（客户端需已安装 [`uv`](https://docs.astral.sh/uv/)）：

#### 1. Claude Desktop 配置 (`~/Library/Application Support/Claude/claude_desktop_config.json` 或 `~/.claude.json`):
```json
{
  "mcpServers": {
    "sap-commerce-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/chriszhangrui/sap-commerce-mcp.git",
        "sap-commerce-mcp"
      ],
      "env": {
        "HAC_URL": "https://localhost:9002",
        "HAC_USER": "admin",
        "HAC_PASS": "nimda"
      }
    }
  }
}
```

#### 2. Antigravity / Gemini CLI 配置 (`~/.gemini/config/mcp_config.json`):
```json
{
  "mcpServers": {
    "sap-commerce-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/chriszhangrui/sap-commerce-mcp.git",
        "sap-commerce-mcp"
      ]
    }
  }
}
```

---

### 方式 B（Claude Code / CLI 一行命令添加）

如果您使用 Claude CLI，可在终端执行一条命令完成注册：

```bash
claude mcp add sap-commerce-mcp -- uvx --from git+https://github.com/chriszhangrui/sap-commerce-mcp.git sap-commerce-mcp
```

---

### 方式 C（全局 `pip` 安装）

```bash
pip install git+https://github.com/chriszhangrui/sap-commerce-mcp.git
```
在客户端配置中，`command` 直接填写 `"sap-commerce-mcp"` 即可。

---

<details>
<summary><b>🛠️ 开发者方式：本地源码二次开发</b>（点击展开）</summary>

如果您需要调试或修改源码：

```bash
git clone https://github.com/chriszhangrui/sap-commerce-mcp.git
cd sap-commerce-mcp

# 创建虚拟环境并安装开发包
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 运行 27 个工具全量回归测试
python test_server.py
```
</details>

---

## 🌟 核心能力概览

- 🏗️ **从零到一 Greenfield 极速建站**：一键完成 `BaseSite`、`BaseStore`、`ProductCatalog`（Staged 与 Online 目录版本）、内容目录（Content Catalog）、同步任务（Sync Job）、多币种、多语言（`zh_TW` 繁体、`en` 英文、`zh` 简体）以及 OCC OAuth 客户端白名单配置。
- 🩺 **Spartacus 前台体检与自动修复**：深度探测 Composable Storefront 的无头配置瓶颈，包括 CORS 跨域白名单缺漏、OCC URL 正则表达式不匹配、OAuth 信任客户端缺失、CMS 首页在线状态，并提供一键自动修复。
- 🏢 **B2B 组织架构与审批流治理**：一键生成企业级多层级 B2B 客户架构，包括总部与子部门 `B2BUnit`、成本中心（Cost Center）、采购预算（Budget）、金额审批阈值（Order Threshold Permission）以及采购员与审批总监账号。
- 🏷️ **Drools 促销规则引擎编排**：全自动编排真实对客场景的 Drools 促销规则（满额立减、买赠送礼、A+B+C 组合套餐、潜在促销达成引导提示），并全自动触发异步非阻塞编译发布。
- ⚡ **底层容器直接交互**：原生执行 FlexibleSearch 数据检索（直接渲染为 Markdown 表格）、ImpEx 事务级数据导入（具备语法严格校验与错误诊断）、Groovy 脚本在 Hybris JVM 容器内的实时热执行。
- 🔍 **Solr 全生命周期运维**：支持进程内全量/增量 Solr 索引重建、监控索引后台任务、目录同步以及 Hybris 内存区域缓存（Region Cache）一键清空。
- 🧠 **脚本资产库与自进化引擎**：内置已验证的 Groovy 与 ImpEx 资产库管理、领域排错知识库（`knowledge_base.json`）自动积累、以及面向 AI 智能体的自进化接口。

---

## 🏛️ 架构设计

```mermaid
flowchart TD
    subgraph AI_Agents ["AI 助手与开发环境"]
        Agent[Claude / Antigravity / Cursor / IDE]
    end

    subgraph MCP_Server ["SAP-Commerce-MCP (sap-commerce-mcp)"]
        Server[MCP 服务端核心 - JSON-RPC Stdio]
        HAC[HAC HTTP 客户端]
        SSO[企业 SSO 自动化认证器]
        Scaffolder[站点与 CMS 编排引擎]
        Doctor[Spartacus 前台体检医生]
        B2B[B2B 组织与审批治理器]
        Promo[Drools 促销规则编排器]
        Solr[Solr 搜索与平台运维]
        Crawler[外部电商站点摄取抓取]
        SelfEvolve[自进化与已验证脚本库]
    end

    subgraph Target_Environments ["SAP Commerce Cloud 目标生态"]
        HybrisJVM["SAP Commerce Cloud (CCL 2211 / CCv2)\n- HAC 管理控制台 & OCC Web 服务\n- Drools 促销规则引擎\n- Solr 检索引擎"]
        Storefront["Composable Storefront (Spartacus)\nAngular / SSR on Node.js"]
    end

    Agent <-->|MCP 协议 (JSON-RPC)| Server
    Server --> HAC
    Server --> SSO
    Server --> Scaffolder
    Server --> Doctor
    Server --> B2B
    Server --> Promo
    Server --> Solr
    Server --> Crawler
    Server --> SelfEvolve

    HAC <-->|HTTPS / Session / CSRF| HybrisJVM
    Doctor <-->|REST / DOM 探测| Storefront
```

---

## 🛠️ 工具套件完整清单 (27 个工具)

### 1. HAC 基础设施与底层执行
| 工具名称 | 关键参数 | 功能描述 |
| :--- | :--- | :--- |
| `hac_configure` | `host`, `username`, `password` | 动态配置目标 Commerce Cloud 实例的 URL、账号密码及会话缓存。 |
| `hac_status` | *(无)* | 检查连接可用性、活跃凭据、会话有效期及 CSRF Token 状态。 |
| `hac_sso_login` | `host` | 唤起可视化浏览器完成 SAP 企业身份源 (SSO) 认证，并持久化缓存 Cookie。 |
| `hac_flexsearch` | `query`, `max_count` | 执行 FlexibleSearch SQL-like 检索，并将结果直接格式化为 Markdown 表格输出。 |
| `hac_impex_import` | `content`, `legacy_mode` | 导入 ImpEx 脚本，提供严格/宽松校验机制及精确的行级错误报告。 |
| `hac_groovy_execute` | `script`, `rollback` | 在 Commerce Cloud JVM 容器内直接执行 Groovy 脚本并捕获控制台输出。 |

### 2. Greenfield 极速建站与 CMS 编排
| 工具名称 | 关键参数 | 功能描述 |
| :--- | :--- | :--- |
| `hac_scaffold_greenfield_site` | `site_id`, `site_name`, `store_id` | 从零到一完整搭建站点：BaseSite、BaseStore、Catalog、同步任务、货币、语言、OCC 匹配规则与 OAuth 客户端。 |
| `hac_site_list` | *(无)* | 罗列系统中所有已配置的 `BaseSite`，展示渠道类型、关联店铺与目录版本状态。 |
| `hac_storefront_cms_scaffold` | `content_catalog`, `featured_products` | 为指定站点生成响应式首页 CMS 组件结构（Banner、轮播图 Carousel、导航树节点）。 |
| `hac_storefront_app_config` | `storefront_dir`, `backend_url` | 自动检查并同步 Spartacus 前端工程所需的 `spartacus-configuration.module.ts` 配置。 |

### 3. Headless Spartacus 前台体检与自动修复
| 工具名称 | 关键参数 | 功能描述 |
| :--- | :--- | :--- |
| `hac_spartacus_doctor` | `site_id`, `storefront_url` | 针对无头前台的 5 维健康体检：BaseSite 状态、OCC 正则匹配、CORS 白名单、OAuth 客户端与首页 CMS 在线发布状态。 |
| `hac_storefront_autofix` | `site_id`, `storefront_url` | 针对体检发现的 Spartacus/OCC 故障进行一键自动化修复（补全跨域、注册 OAuth、同步发布 CMS）。 |

### 4. B2B 组织层级与审批流治理
| 工具名称 | 关键参数 | 功能描述 |
| :--- | :--- | :--- |
| `hac_b2b_scaffold_org` | `root_unit_id`, `budget_amount` | 搭建完整企业 B2B 客户组织树：总部、子采购部门、成本中心、预算限额、审批阈值及采购员/审批官角色账号。 |
| `hac_b2b_org_doctor` | `user_id` | 深度体检 B2B 用户：组织隶属、成本中心有效性、审批权限链条、安全用户组及结算下单权限。 |

### 5. Drools 促销规则引擎编排
| 工具名称 | 关键参数 | 功能描述 |
| :--- | :--- | :--- |
| `hac_promotion_scaffold` | `rule_code`, `promotion_type` | 自动化编排 Drools 规则：订单金额满减、买 X 赠 Y、多品搭售（A+B+C）以及未达门槛引导差额提示，并触发编译发布。 |
| `hac_promotion_list` | `rule_code`, `status` | 检索与过滤促销规则列表，显示优先级、发布状态及多语言文案触发信息。 |

### 6. Solr 搜索、目录同步与运维
| 工具名称 | 关键参数 | 功能描述 |
| :--- | :--- | :--- |
| `hac_solr_reindex` | `facet_config_name`, `mode` | 触发进程内全量 (`FULL`) 或增量 (`UPDATE`) Solr 索引重建任务。 |
| `hac_solr_status` | *(无)* | 查询 Solr 索引任务的执行耗时与最新 CronJob 状态。 |
| `hac_catalog_sync` | `catalog_id`, `source_version` | 触发产品目录版本同步任务（`Staged` 阶段 -> `Online` 在线）。 |
| `hac_cache_clear` | *(无)* | 一键清空 Commerce 底层 Region Cache 内存缓存。 |
| `hac_check_i18n_completeness` | `catalog_id`, `target_langs` | 全量核验主数据与促销的多语言完整性（覆盖 `zh_TW`、`en`、`zh`）。 |

### 7. 外部电商站点摄取、脚本资产库与自进化
| 工具名称 | 关键参数 | 功能描述 |
| :--- | :--- | :--- |
| `hac_ingest_external_storefront` | `store_url`, `platform_type` | 抓取外部独立站（Shopify、WooCommerce 等）商品主数据，一键转为 Hybris 标准 ImpEx。 |
| `hac_library_list` | `category`, `search` | 检索与浏览本地已验证的 Groovy 与 ImpEx 脚本资产库。 |
| `hac_library_get` | `script_id` | 按标识提取归档的历史脚本全文。 |
| `hac_self_diagnose` | *(无)* | 对 MCP 自身核心模块、依赖组件、资产库与经验库进行自我健康体检。 |
| `hac_self_improve` | `target_file`, `description` | 自动内化与增强 MCP 自身能力，实现工具集的自生长。 |
| `hac_record_learning` | `pattern_name`, `solution` | 将排错经验与实战最佳实践自动归档沉淀至 `knowledge_base.json`。 |

---

## 🏆 实战标杆案例（Battle-Tested Scenarios）

### 案例一：某世界 500 强快消饮料企业 eB2B 数字化商城（亚太区）
- **全生命周期建站**：通过 `hac_scaffold_greenfield_site` 一键开辟专属 B2B 站点，绑定港币 HKD 与美元 USD，启用繁体中文 `zh_TW` 与英文 `en`；
- **100+ 款饮品主数据入库**：管理 13 大饮品系列（汽水、无糖、果汁、水）与多个经典品牌，通过 `hac_impex_import` 和 `hac_catalog_sync` 实现 Staged 到 Online 双目录同步；
- **Drools 复杂组合促销编排**：利用 `hac_promotion_scaffold` 编排【A+B+C 汽水大礼包】组合促销，当购物车集齐指定饮品时自动赠送礼品，且中英文引导文案与 Drools 规则编译一次性就绪；
- **Solr 即时全量重建**：通过 `hac_solr_reindex` 触发索引重构，前台搜索无缝立即可见。

### 案例二：某全球医疗器械企业 B2B 组织层级与审批流治理
- **多层级组织构建**：通过 `hac_b2b_scaffold_org` 搭建企业总部与多个二级采购部门单位；
- **成本中心与审批阈值**：配置季度限额的 `B2BBudget` 与单笔采购超额触发总监审批权限；
- **账号体检与放行**：通过 `hac_b2b_org_doctor` 针对采购经理账号进行 6 维体检，精确诊断为何订单被 HOLD 并自动修复用户组。

---

## 💡 实战避坑经验库（Best Practices）

基于 `knowledge_base.json` 实战沉淀的避坑指南：
1. **语言代码规范**：SAP Commerce Cloud 标准 C2L 表中简体中文代码为 `zh` 而非 `zh_CN`（繁体中文为 `zh_TW`）。MCP 在生成 ImpEx 时已内置自动归一化处理。
2. **B2B 预算日期区间**：`B2BBudget` 创建必须携带精确格式 `dateRange[dateformat=dd.MM.yyyy hh:mm:ss,allownull=true]`，且必须关联根级 `B2BUnit`。
3. **绕过 Solr CronJob 调度卡顿**：当系统后台存在排队任务时，通过 `hac_solr_reindex` 直接调用 JVM 内 `IndexerService.performFullIndex(cfg)` 实行进程内同步构建，避免等待 CronJob 调度器释放。

---

## ⚙️ 环境变量速查

| 变量名 | 默认值 | 作用说明 |
| :--- | :--- | :--- |
| `HAC_URL` | `https://localhost:9002` | 目标 Commerce Cloud HAC 控制台根地址 |
| `HAC_USER` | `admin` | HAC 管理员账号 |
| `HAC_PASS` | `nimda` | HAC 管理员密码 |
| `HAC_STORAGE_PATH` | `~/.mcp-servers/sap-commerce-mcp/hac_storage_state.json` | SSO 浏览器会话 Cookie 缓存路径 |
| `SPARTACUS_PROJECT_PATH` | `~/sap-ai-commerce-demo/spartacus-storefront` | 本地 Spartacus 前端工程根目录 |

---

## 📄 开源许可

本项目基于 [MIT License](LICENSE) 开源许可协议。
