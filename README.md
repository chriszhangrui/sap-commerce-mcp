# SAP Commerce Cloud MCP Server (`SAP-Commerce-MCP`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![SAP Commerce Cloud](https://img.shields.io/badge/SAP%20Commerce%20Cloud-2211%20%7C%20CCv2-008FD3.svg)](https://help.sap.com/docs/SAP_COMMERCE_CLOUD)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md) | [中文说明](README_ZH.md)

**SAP-Commerce-MCP** (`sap-commerce-mcp`) is an enterprise-grade Model Context Protocol (MCP) server that empowers AI assistants (Claude, Antigravity, Cursor, etc.) to directly control, automate, orchestrate, and self-heal **SAP Commerce Cloud (Hybris)** environments and **Headless Composable Storefronts (Spartacus)**.

Far beyond a basic Hybris Administration Console (HAC) bridge, it functions as a comprehensive Commerce Cloud Copilot with Greenfield site provisioning, B2B organizational governance, Drools promotion engine orchestration, headless Spartacus storefront diagnostics, Solr search indexing, catalog synchronization, and an agentic self-evolution engine.

---

## 🌟 Key Capabilities at a Glance

- 🏗️ **Zero-to-One Greenfield Provisioning**: Instant scaffolding of `BaseSite`, `BaseStore`, `ProductCatalog` (Staged & Online), Content Catalogs, Sync Jobs, Multi-currency, Multi-language (`zh_TW`, `en`, `zh_CN`), and OCC OAuth client credentials.
- 🩺 **Headless Spartacus Doctor & Auto-Healing**: Deep diagnostics for Composable Storefronts, detecting CORS whitelist gaps, OCC URL regex mismatches, OAuth client registrations, and CMS online status with one-click automated remediation.
- 🏢 **B2B Organization Governance**: Automated setup and validation of multi-tiered `B2BUnit` hierarchies, `B2BBudget`, `B2BCostCenter`, `B2BOrderThresholdPermission` approval limits, and demo buyer/approver personas.
- 🏷️ **Drools Promotion Engine Orchestration**: Code-free provisioning of B2B/B2C promotion rules (Spend Thresholds, Free Gifts, A+B+C Bundles, and Potential Promotion reminders) with automatic Drools rule compilation and publishing.
- ⚡ **Direct Hybris Runtime Control**: Seamless execution of FlexibleSearch queries (rendered as Markdown tables), transactional ImpEx imports with strict validation, and Groovy scripts executed live in the Hybris JVM container.
- 🔍 **Solr Indexing & Platform Ops**: In-process full/update Solr reindexing, cronjob monitoring, catalog synchronization, and Hybris Region Cache clearing.
- 🧠 **Self-Evolution & Proven Script Library**: Built-in script asset manager archiving verified Groovy/ImpEx scripts, domain knowledge base accumulating troubleshooting experience, and self-improving meta-tools.

---

## 🏛️ Architecture Overview

```mermaid
flowchart TD
    subgraph AI_Agents ["AI Assistants & IDEs"]
        Agent[Claude / Antigravity / Cursor]
    end

    subgraph MCP_Server ["SAP-Commerce-MCP (sap-commerce-mcp)"]
        Server[MCP Server Core - JSON-RPC Stdio]
        HAC[HAC HTTP Client]
        SSO[Corporate SSO Authenticator]
        Scaffolder[Site & CMS Scaffolder]
        Doctor[Spartacus Doctor]
        B2B[B2B Org Helper]
        Promo[Drools Promotion Engine]
        Solr[Solr & Platform Ops]
        Crawler[Storefront Ingestion]
        SelfEvolve[Self-Evolution & Script Library]
    end

    subgraph Target_Environments ["SAP Commerce Cloud Ecosystem"]
        HybrisJVM["SAP Commerce Cloud (CCL 2211 / CCv2)\n- HAC & Web Services (OCC)\n- Drools Rule Engine\n- Solr Search Engine"]
        Storefront["Composable Storefront (Spartacus)\nAngular / SSR on Node.js"]
    end

    Agent <-->|MCP Protocol (JSON-RPC)| Server
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
    Doctor <-->|REST / DOM Probe| Storefront
```

---

## 🛠️ Complete Tool Suite (27 Tools)

### 1. HAC Infrastructure & Authentication
| Tool Name | Description |
| :--- | :--- |
| `hac_configure` | Dynamically configures the target Commerce Cloud instance URL, credentials, and SSO session cache path. |
| `hac_status` | Checks connection health, active credentials, session validity, and CSRF token status. |
| `hac_sso_login` | Launches an interactive headed browser session to handle corporate SSO (e.g. SAP Identity / Microsoft Entra) and caches the session cookie. |
| `hac_flexsearch` | Executes FlexibleSearch queries and formats tabular output directly into Markdown. |
| `hac_impex_import` | Imports ImpEx scripts with strict/relaxed validation and detailed error reporting. |
| `hac_groovy_execute` | Executes Groovy scripts directly inside the Commerce Cloud JVM container. |

### 2. Greenfield Site Provisioning & CMS Orchestration
| Tool Name | Description |
| :--- | :--- |
| `hac_scaffold_greenfield_site` | Fully automates new site creation: BaseSite, BaseStore, Catalogs (Staged & Online), Sync Jobs, Currencies, Languages, OCC URL regex, and trusted OAuth clients. |
| `hac_site_list` | Lists all configured `BaseSite` models, channels, stores, and catalog linkages. |
| `hac_storefront_cms_scaffold` | Scaffolds responsive homepage CMS structures (banners, carousels, responsive navigation nodes). |
| `hac_storefront_app_config` | Generates ready-to-use Spartacus `spartacus-configuration.module.ts` code for frontend alignment. |

### 3. Headless Spartacus Diagnostics & Auto-Healing
| Tool Name | Description |
| :--- | :--- |
| `hac_spartacus_doctor` | Comprehensive headless storefront health check: BaseSite existence, OCC URL regex patterns, CORS allowed origins, OAuth client registration, and Homepage CMS status. |
| `hac_storefront_autofix` | Automatically remediates identified Spartacus/OCC bottlenecks (CORS whitelisting, OAuth registration, staged-to-online CMS publishing). |

### 4. B2B Organization Hierarchy & Governance
| Tool Name | Description |
| :--- | :--- |
| `hac_b2b_scaffold_org` | Scaffolds enterprise B2B customer hierarchy: Root Unit, sub-departments, Cost Centers, Budgets, Approval Thresholds, and Buyer/Approver demo accounts. |
| `hac_b2b_org_doctor` | In-depth audit of a B2B user: Unit hierarchy, assigned cost centers, approval chains, user groups, and checkout authorizations. |

### 5. Drools Promotion Engine Orchestration
| Tool Name | Description |
| :--- | :--- |
| `hac_promotion_scaffold` | Automates Drools promotion rules: Order Total Threshold discounts, Buy X Get Y Free Gifts, Multi-Product Bundles (A+B+C), and Potential Promotion reminders. |
| `hac_promotion_list` | Lists and filters active `PromotionSourceRule` models across modules, displaying priority, status, and triggers. |

### 6. Solr Search, Catalog Sync & Platform Ops
| Tool Name | Description |
| :--- | :--- |
| `hac_solr_reindex` | Triggers in-process full or incremental Solr reindexing for target facet search configurations. |
| `hac_solr_status` | Queries the status and duration of running Solr indexer cronjobs. |
| `hac_catalog_sync` | Triggers catalog version synchronization jobs (`Staged` -> `Online`). |
| `hac_cache_clear` | Clears the Hybris Region Cache in memory. |
| `hac_check_i18n_completeness` | Audits localization completeness across product catalogs (detects missing translations in `zh_TW`, `en`, `zh_CN`). |

### 7. External Ingestion, Script Library & Self-Evolution
| Tool Name | Description |
| :--- | :--- |
| `hac_ingest_external_storefront` | Crawls external e-commerce sites (Shopify, WooCommerce, Magento) to extract products and generate Hybris-compatible ImpEx. |
| `hac_library_list` | Browses the local repository of proven, verified Groovy and ImpEx scripts. |
| `hac_library_get` | Retrieves the full content of an archived script by identifier. |
| `hac_self_diagnose` | Performs self-diagnostics on the MCP server itself (module health, script library count, knowledge base rules). |
| `hac_self_improve` | Enhances server capability and internalizes new operational tools. |
| `hac_record_learning` | Persists domain knowledge, error patterns, and troubleshooting rules into `knowledge_base.json`. |

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/chriszhangrui/sap-commerce-mcp.git
cd sap-commerce-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verification

Run the built-in JSON-RPC stdio verification suite:

```bash
python test_server.py
```

Expected output:
```text
✓ Initialize: sap-commerce-mcp
✓ Registered tools count: 27
✓ Self-Diagnose Preview: 🟢 核心模块全部正常就绪
...
🎉 ALL 27 MCP TOOLS OPERATIONAL & VERIFIED OVER JSON-RPC STDIO!
```

---

## ⚙️ Configuration

Add `sap-commerce-mcp` to your MCP configuration file.

### For Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json` or `~/.claude.json`):

```json
{
  "mcpServers": {
    "sap-commerce-mcp": {
      "command": "/path/to/sap-commerce-mcp/venv/bin/python",
      "args": [
        "/path/to/sap-commerce-mcp/server.py"
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

### For Antigravity / Gemini CLI (`~/.gemini/config/mcp_config.json`):

```json
{
  "mcpServers": {
    "sap-commerce-mcp": {
      "command": "/path/to/sap-commerce-mcp/venv/bin/python",
      "args": [
        "/path/to/sap-commerce-mcp/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

---

## 💡 Example Prompt Scenarios

Once connected, your AI assistant can execute complex Commerce tasks directly from natural language:

### Scenario 1: Greenfield B2B Storefront Scaffolding
> *"Scaffold a new B2B site called `swire-beverages` with currency HKD and USD, languages zh_TW and en, link it to powertools catalogs, and verify Spartacus headless readiness."*

### Scenario 2: Drools Promotion Orchestration
> *"Create an A+B+C sparkling beverage bundle promotion in the powertoolsPromoGrp module: when a customer buys Coke, Sprite, and Fanta together, gift them 1 case of Monster Energy. Ensure the message is localized in English and Traditional Chinese."*

### Scenario 3: B2B Organization & Approval Flow Diagnosis
> *"Run an audit on B2B buyer `buyer.mindray_global@demo.com`. Why is their checkout order being held for approval? Check their cost center and approval threshold."*

### Scenario 4: Live Data Inspection
> *"Execute a FlexibleSearch to list the top 10 products in powertoolsProductCatalog Online version ordered by creation time."*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
