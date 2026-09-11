# SAP Commerce Cloud MCP 服务器 (`SAP-Commerce-MCP`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![SAP Commerce Cloud](https://img.shields.io/badge/SAP%20Commerce%20Cloud-2211%20%7C%20CCv2-008FD3.svg)](https://help.sap.com/docs/SAP_COMMERCE_CLOUD)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md) | [中文说明](README_ZH.md)

**SAP-Commerce-MCP** (`sap-commerce-mcp`) 是专为 **SAP Commerce Cloud (Hybris)** 与 **Headless Composable Storefront (Spartacus)** 打造的企业级 Model Context Protocol (MCP) 服务端。它赋予 AI 助手（Claude、Antigravity、Cursor 等）直接操控、运维、编排与自愈 Commerce 系统的全套原生能力。

它远不止是一个简单的 Hybris 管理控制台 (HAC) 接口封装，而是一个具备**站点从零搭建**、**B2B 组织层级与审批流治理**、**Drools 促销规则自动化编排**、**Spartacus 无头前台深度体检与自愈**、**Solr 搜索运维**以及**智能经验自沉淀**的全面副驾驶平台。

---

## 🌟 核心能力概览

- 🏗️ **从零到一 Greenfield 极速建站**：一键完成 `BaseSite`、`BaseStore`、`ProductCatalog`（Staged 与 Online 目录版本）、内容目录（Content Catalog）、同步任务（Sync Job）、多币种、多语言（`zh_TW` 繁体、`en` 英文、`zh_CN` 简体）以及 OCC OAuth 客户端白名单配置。
- 🩺 **Spartacus 前台体检与自动修复**：深度探测 Composable Storefront 的无头配置瓶颈，包括 CORS 跨域白名单缺漏、OCC URL 正则表达式不匹配、OAuth 信任客户端缺失、CMS 首页在线状态，并提供一键自动修复。
- 🏢 **B2B 组织架构与审批流治理**：一键生成企业级多层级 B2B 客户架构，包括总部与子部门 `B2BUnit`、成本中心（Cost Center）、采购预算（Budget）、金额审批阈值（Order Threshold Permission）以及采购员与审批总监账号。
- 🏷️ **Drools 促销规则引擎编排**：全自动编排太古可口可乐等真实对客场景的 Drools 促销规则（满额立减、买赠送礼、A+B+C 组合套餐、潜在促销达成引导提示），并全自动触发异步非阻塞编译发布。
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
| 工具名称 | 功能描述 |
| :--- | :--- |
| `hac_configure` | 动态配置目标 Commerce Cloud 实例的 URL、账号密码及 SSO 缓存路径。 |
| `hac_status` | 检查连接可用性、活跃凭据、会话有效期及 CSRF Token 状态。 |
| `hac_sso_login` | 唤起可视化浏览器完成 SAP 企业身份源 (SSO) 认证，并持久化缓存 Cookie。 |
| `hac_flexsearch` | 执行 FlexibleSearch SQL-like 检索，并将结果直接格式化为 Markdown 表格输出。 |
| `hac_impex_import` | 导入 ImpEx 脚本，提供严格/宽松校验机制及精确的行级错误报告。 |
| `hac_groovy_execute` | 在 Commerce Cloud JVM 容器内直接执行 Groovy 脚本并捕获控制台输出。 |

### 2. Greenfield 极速建站与 CMS 编排
| 工具名称 | 功能描述 |
| :--- | :--- |
| `hac_scaffold_greenfield_site` | 从零到一完整搭建站点：BaseSite、BaseStore、Catalog、同步任务、货币、语言、OCC 匹配规则与 OAuth 客户端。 |
| `hac_site_list` | 罗列系统中所有已配置的 `BaseSite`，展示渠道类型、关联店铺与目录版本状态。 |
| `hac_storefront_cms_scaffold` | 为指定站点生成响应式首页 CMS 组件结构（Banner、轮播图 Carousel、导航树节点）。 |
| `hac_storefront_app_config` | 自动生成 Spartacus 前端工程所需的 `spartacus-configuration.module.ts` 源码配置。 |

### 3. Headless Spartacus 前台体检与自动修复
| 工具名称 | 功能描述 |
| :--- | :--- |
| `hac_spartacus_doctor` | 针对无头前台的 5 维健康体检：BaseSite 状态、OCC 正则匹配、CORS 白名单、OAuth 客户端与首页 CMS 在线发布状态。 |
| `hac_storefront_autofix` | 针对体检发现的 Spartacus/OCC 故障进行一键自动化修复（补全跨域、注册 OAuth、同步发布 CMS）。 |

### 4. B2B 组织层级与审批流治理
| 工具名称 | 功能描述 |
| :--- | :--- |
| `hac_b2b_scaffold_org` | 搭建完整企业 B2B 客户组织树：总部、子采购部门、成本中心、预算限额、审批阈值及采购员/审批官角色账号。 |
| `hac_b2b_org_doctor` | 深度体检 B2B 用户：组织隶属、成本中心有效性、审批权限链条、安全用户组及结算下单权限。 |

### 5. Drools 促销规则引擎编排
| 工具名称 | 功能描述 |
| :--- | :--- |
| `hac_promotion_scaffold` | 自动化编排 Drools 规则：订单金额满减、买 X 赠 Y、多品搭售（A+B+C）以及未达门槛引导差额提示，并触发编译发布。 |
| `hac_promotion_list` | 检索与过滤促销规则列表，显示优先级、发布状态及多语言文案触发信息。 |

### 6. Solr 搜索、目录同步与运维
| 工具名称 | 功能描述 |
| :--- | :--- |
| `hac_solr_reindex` | 触发进程内全量或增量 Solr 索引重建任务。 |
| `hac_solr_status` | 查询 Solr 索引任务的执行耗时与最新 CronJob 状态。 |
| `hac_catalog_sync` | 触发产品目录版本同步任务（`Staged` 阶段 -> `Online` 在线）。 |
| `hac_cache_clear` | 一键清空 Commerce 底层 Region Cache 内存缓存。 |
| `hac_check_i18n_completeness` | 全量核验主数据与促销的多语言完整性（覆盖 `zh_TW`、`en`、`zh_CN`）。 |

### 7. 外部电商站点摄取、脚本资产库与自进化
| 工具名称 | 功能描述 |
| :--- | :--- |
| `hac_ingest_external_storefront` | 抓取外部独立站（Shopify、WooCommerce、Magento 等）商品主数据，一键转为 Hybris 标准 ImpEx。 |
| `hac_library_list` | 检索与浏览本地已验证的 Groovy 与 ImpEx 脚本资产库。 |
| `hac_library_get` | 按标识提取归档的历史脚本全文。 |
| `hac_self_diagnose` | 对 MCP 自身核心模块、依赖组件、资产库与经验库进行自我健康体检。 |
| `hac_self_improve` | 自动内化与增强 MCP 自身能力，实现工具集的自生长。 |
| `hac_record_learning` | 将排错经验与实战最佳实践自动归档沉淀至 `knowledge_base.json`。 |

---

## 🚀 快速上手

### 1. 安装环境

克隆仓库并安装 Python 依赖：

```bash
git clone https://github.com/chriszhangrui/sap-commerce-mcp.git
cd sap-commerce-mcp

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装必要依赖
pip install -r requirements.txt
```

### 2. 运行测试验证

执行内置的完整 JSON-RPC 自动化测试套件：

```bash
python test_server.py
```

预期输出：
```text
--- 1. Testing Initialize ---
✓ Initialize: sap-commerce-mcp

--- 2. Testing tools/list ---
✓ Registered tools count: 27
...
🎉 ALL 27 MCP TOOLS (INCLUDING COMPOSABLE STOREFRONT ORCHESTRATION) OPERATIONAL & VERIFIED OVER JSON-RPC STDIO!
```

---

## ⚙️ MCP 客户端接入配置

将 `sap-commerce-mcp` 加入到你的客户端配置文件中：

### Claude Desktop 配置 (`~/Library/Application Support/Claude/claude_desktop_config.json` 或 `~/.claude.json`):

```json
{
  "mcpServers": {
    "sap-commerce-mcp": {
      "type": "stdio",
      "command": "/你的路径/sap-commerce-mcp/venv/bin/python",
      "args": [
        "/你的路径/sap-commerce-mcp/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "HAC_URL": "https://localhost:9002",
        "HAC_USER": "admin",
        "HAC_PASS": "nimda"
      }
    }
  }
}
```

### Antigravity / Gemini CLI 配置 (`~/.gemini/config/mcp_config.json`):

```json
{
  "mcpServers": {
    "sap-commerce-mcp": {
      "command": "/你的路径/sap-commerce-mcp/venv/bin/python",
      "args": [
        "/你的路径/sap-commerce-mcp/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

---

## 💡 典型自然语言调用范例

接入后，你可以在 AI 助手中直接用自然语言执行复杂商业指令：

### 场景一：从零创建太古可口可乐 eB2B 站点
> *"帮我搭建一个名为 `swire-beverages` 的 B2B 站点，货币支持 HKD 与 USD，语言启用繁体中文 zh_TW 和英文 en，挂载到 powertools 目录并校验 Spartacus 无头访问就绪状态。"*

### 场景二：Drools 促销规则编排与多语言发布
> *"在 powertoolsPromoGrp 促销组中创建【A+B+C 经典汽水买赠】：购物车同时包含可乐、无糖可乐与雪碧各1箱时，自动赠送1箱 Monster 魔爪能量饮料，中英文触发文案都要补全并完成编译发布。"*

### 场景三：B2B 审批流体检与诊断
> *"排查迈瑞医疗采购员 `buyer.mindray_global@demo.com`，为什么在前端结算下单时提示超出预算？检查其审批流链条与所属成本中心。"*

### 场景四：实时底层数据巡检
> *"执行 FlexibleSearch 查一下 powertoolsProductCatalog Online 版本中最近创建的前 10 款商品及其价格与库存。"*

---

## 📄 开源许可

本项目基于 [MIT License](LICENSE) 开源许可协议。
