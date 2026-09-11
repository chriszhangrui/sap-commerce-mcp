#!/usr/bin/env python3
import os
import sys
import json
from typing import Optional, Dict, Any, List

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.mcpserver import MCPServer
from hac_client import HACClient
from sso_helper import perform_interactive_sso, DEFAULT_STORAGE_PATH
from solr_sync_helper import SolrSyncHelper
from spartacus_doctor import SpartacusDoctor
from b2b_org_helper import B2BOrgHelper
from storefront_crawler import StorefrontCrawler
from site_scaffolder import SiteScaffolder
from script_manager import ScriptManager
from self_improver import SelfImprover
from promotion_helper import PromotionHelper
from storefront_helper import StorefrontHelper

# Initialize global MCP server
mcp = MCPServer(
    name="sap-commerce-mcp",
    title="SAP Commerce Cloud (eB2B/B2C) Automation, Governance & Self-Evolution MCP Server",
    version="3.0.0",
    description="Model Context Protocol Server for SAP Commerce Cloud (Hybris). Features automated site scaffolding, headless Spartacus/Composable Storefront diagnostics & CMS orchestration, B2B org governance, external storefront crawling, proven script library archiving, Drools promotion engine, and self-evolution capabilities."
)

# Global persistent client & helpers
_client = HACClient()
_solr_sync = SolrSyncHelper(_client)
_doctor = SpartacusDoctor(_client)
_b2b = B2BOrgHelper(_client)
_crawler = StorefrontCrawler(_client)
_scaffolder = SiteScaffolder(_client)
_script_mgr = ScriptManager()
_self_improver = SelfImprover()
_promo = PromotionHelper(_client, _script_mgr)
_storefront = StorefrontHelper(_client, _script_mgr)

def _update_helpers(client: HACClient):
    global _client, _solr_sync, _doctor, _b2b, _crawler, _scaffolder, _promo, _storefront
    _client = client
    _solr_sync = SolrSyncHelper(_client)
    _doctor = SpartacusDoctor(_client)
    _b2b = B2BOrgHelper(_client)
    _crawler = StorefrontCrawler(_client)
    _scaffolder = SiteScaffolder(_client)
    _promo = PromotionHelper(_client, _script_mgr)
    _storefront = StorefrontHelper(_client, _script_mgr)

@mcp.tool()
def hac_configure(
    host: str,
    username: str = "admin",
    password: str = "nimda",
    sso_storage_path: Optional[str] = None
) -> str:
    """
    Configures the target SAP Commerce HAC instance and credentials.
    """
    client = HACClient(
        base_url=host,
        username=username,
        password=password,
        sso_storage_path=sso_storage_path
    )
    _update_helpers(client)
    try:
        _client.ensure_authenticated()
        return f"Successfully connected and authenticated with HAC at {_client.base_url} (User: {username})"
    except Exception as e:
        return f"Configured host to {_client.base_url}, but authentication check failed: {e}. If protected by SAP SSO, run `hac_sso_login`."

@mcp.tool()
def hac_status() -> str:
    """
    Checks the current status and authentication of the configured HAC connection.
    """
    try:
        _client.ensure_authenticated()
        csrf = _client.get_csrf_token()
        return f"Status: CONNECTED & AUTHENTICATED\nBase URL: {_client.base_url}\nUser: {_client.username}\nCSRF Active: {'Yes' if csrf else 'No'}"
    except Exception as e:
        return f"Status: DISCONNECTED or UNAUTHENTICATED\nBase URL: {_client.base_url}\nError: {e}"

@mcp.tool()
def hac_sso_login(host: Optional[str] = None) -> str:
    """
    Launches a headed browser window for the user to complete SAP internal SSO authentication.
    """
    target = host or _client.base_url
    print(f"[SSO] Launching interactive login for {target}...", file=sys.stderr)
    ok = perform_interactive_sso(hac_url=target)
    if ok:
        _client.load_sso_session()
        try:
            _client.ensure_authenticated()
            return f"SAP SSO login successful! Authenticated session updated for {_client.base_url}."
        except Exception as e:
            return f"SSO session captured, but HAC verification failed: {e}"
    else:
        return "SSO login was canceled or timed out."

@mcp.tool()
def hac_flexsearch(
    query: str,
    max_count: int = 50,
    host: Optional[str] = None
) -> str:
    """
    Executes a FlexibleSearch SQL query on the SAP Commerce database.
    """
    client = _client
    if host and host != client.base_url:
        client = HACClient(base_url=host, username=_client.username, password=_client.password)
    
    res = client.execute_flexsearch(query=query, max_count=max_count)
    if res.get("exception"):
        return f"Error executing FlexibleSearch:\n{res.get('exception')}\n{res.get('exceptionStackTrace', '')}"
    
    headers = res.get("headers", [])
    result_list = res.get("resultList", [])
    count = res.get("resultCount", len(result_list))
    time_ms = res.get("executionTime", 0)

    if not headers:
        return f"Query executed in {time_ms} ms with {count} results (no headers returned)."
    
    lines = [
        f"**Results:** {count} rows | **Time:** {time_ms} ms",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]
    for row in result_list:
        row_str = [str(col).replace("\n", " ").replace("|", "\\|") for col in row]
        lines.append("| " + " | ".join(row_str) + " |")
    
    return "\n".join(lines)

@mcp.tool()
def hac_impex_import(
    script_content: Optional[str] = None,
    file_path: Optional[str] = None,
    validation_enum: str = "IMPORT_STRICT",
    legacy_mode: bool = False,
    enable_code_execution: bool = True,
    max_threads: int = 1,
    archive_name: Optional[str] = None,
    client_name: Optional[str] = None,
    host: Optional[str] = None
) -> str:
    """
    Imports an ImpEx script into the SAP Commerce instance. Automatically archives successful scripts to script library.
    """
    content = script_content
    if not content:
        if not file_path or not os.path.isfile(file_path):
            return "Error: You must provide either non-empty `script_content` or a valid `file_path`."
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {e}"
    
    client = _client
    if host and host != client.base_url:
        client = HACClient(base_url=host, username=_client.username, password=_client.password)
    
    res = client.import_impex(
        script_content=content,
        validation_enum=validation_enum,
        legacy_mode=legacy_mode,
        enable_code_execution=enable_code_execution,
        max_threads=max_threads
    )
    
    status = res.get("status", "UNKNOWN")
    msg = res.get("message", "")
    dump = res.get("dump", "")
    
    out = [f"**ImpEx Import Status:** {status}", f"**Message:** {msg}"]
    
    # Auto-archive if successful
    if status in ["SUCCESS", "FINISHED"]:
        entry_name = archive_name or (os.path.basename(file_path) if file_path else "imported_impex")
        entry = _script_mgr.archive_script(
            content=content,
            script_type="impex",
            name=entry_name,
            category="general_impex",
            description=msg,
            client_name=client_name
        )
        out.append(f"📦 **已自动归档至统一脚本库:** `{entry['path']}` (ID: `{entry['id']}`)")
    elif dump:
        out.append(f"**Error / Dump Details:**\n```\n{dump}\n```")
        
    return "\n".join(out)

@mcp.tool()
def hac_groovy_execute(
    script: Optional[str] = None,
    file_path: Optional[str] = None,
    commit: bool = True,
    archive_name: Optional[str] = None,
    client_name: Optional[str] = None,
    host: Optional[str] = None
) -> str:
    """
    Executes a Groovy script in the HAC Scripting Console. Automatically archives successful scripts to script library.
    """
    code = script
    if not code:
        if not file_path or not os.path.isfile(file_path):
            return "Error: You must provide either non-empty `script` or a valid `file_path`."
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {e}"

    client = _client
    if host and host != client.base_url:
        client = HACClient(base_url=host, username=_client.username, password=_client.password)

    res = client.execute_groovy(script=code, commit=commit)
    
    out = []
    output_text = res.get("outputText", "").strip()
    exec_result = res.get("executionResult", "")
    stacktrace = res.get("stacktraceText", "").strip()

    if output_text:
        out.append(f"**Console Output:**\n```\n{output_text}\n```")
    if exec_result is not None and str(exec_result).strip():
        out.append(f"**Execution Return Value:**\n```\n{exec_result}\n```")
    if stacktrace:
        out.append(f"**Stacktrace / Error:**\n```\n{stacktrace}\n```")
    
    # Auto-archive if successful without stacktrace
    if not stacktrace and not res.get("exception"):
        entry_name = archive_name or (os.path.basename(file_path) if file_path else "executed_groovy")
        entry = _script_mgr.archive_script(
            content=code,
            script_type="groovy",
            name=entry_name,
            category="general_groovy",
            description="Groovy script executed successfully",
            client_name=client_name
        )
        out.append(f"📦 **已自动归档至统一脚本库:** `{entry['path']}` (ID: `{entry['id']}`)")
    
    if not out:
        if res.get("exception"):
            return f"Execution Error: {res.get('exception')}"
        return "Groovy script executed successfully with no output."

    return "\n\n".join(out)

@mcp.tool()
def hac_scaffold_greenfield_site(
    site_id: str,
    site_name: str,
    channel: str = "B2B",
    currency: str = "USD",
    languages: Optional[List[str]] = None,
    storefront_origin: str = "http://localhost:4200",
    content_catalog: Optional[str] = None,
    delivery_countries: Optional[List[str]] = None,
    setup_b2b_org: bool = True,
    monthly_budget: float = 50000.0,
    approval_threshold: float = 200.0
) -> str:
    """
    Scaffolds a complete greenfield SAP Commerce site, BaseStore, ProductCatalog,
    OCC headless URL patterns, OAuth clients, and optional B2B organization hierarchy.
    """
    res = _scaffolder.scaffold_site(
        site_id=site_id,
        site_name=site_name,
        channel=channel,
        currency=currency,
        languages=languages,
        storefront_origin=storefront_origin,
        content_catalog=content_catalog,
        delivery_countries=delivery_countries,
        setup_b2b_org=setup_b2b_org,
        monthly_budget=monthly_budget,
        approval_threshold=approval_threshold
    )
    
    out = [
        f"🚀 **Greenfield Site Scaffolding Completed: {site_name}**",
        f"- **BaseSite UID:** `{res['site_id']}` (Channel: `{res['channel']}`)",
        f"- **BaseStore UID:** `{res['base_store']}`",
        f"- **Product Catalog:** `{res['product_catalog']}` (Staged & Online)",
        f"- **Brand Content Catalog:** `{res['brand_content_catalog']}` (Private Homepage/Banners)",
        f"- **Fallback Template:** `{res['fallback_content_catalog']}` (Shared Cart/Checkout)",
        f"- **Bound Catalogs:** `{', '.join(res['content_catalogs'])}`",
        f"- **ImpEx Status:** `{res['impex_status']}` ({res['impex_message']})",
    ]
    if res.get("b2b_scaffold"):
        out.append(f"\n{res['b2b_scaffold']}")
    
    out.append(f"\n📋 **Recommended Spartacus Configuration (`spartacus-configuration.module.ts`):**\n```typescript\n{res['spartacus_config']}\n```")
    return "\n".join(out)

@mcp.tool()
def hac_site_list(lang: str = "zh") -> str:
    """
    Lists all CMSSites in the SAP Commerce instance with their BaseStore,
    ProductCatalog, ContentCatalogs, Languages, Currencies, and active status.
    Essential for enterprise multi-brand group governance.
    """
    return _scaffolder.list_sites(lang=lang)

@mcp.tool()
def hac_spartacus_doctor(
    site_id: str = "powertools-spa",
    storefront_url: str = "http://localhost:4200",
    lang: str = "zh"
) -> str:
    """
    Performs a full headless readiness health check for a Spartacus storefront and Commerce Cloud BaseSite.
    """
    return _doctor.diagnose(site_id=site_id, storefront_url=storefront_url, lang=lang)

@mcp.tool()
def hac_b2b_scaffold_org(
    root_unit_id: str,
    root_unit_name: str,
    sub_units: Optional[List[Dict[str, Any]]] = None,
    currency: str = "USD",
    languages: Optional[List[str]] = None,
    monthly_budget: float = 50000.0,
    approval_threshold: float = 200.0,
    buyer_name: Optional[str] = None,
    buyer_email: Optional[str] = None,
    approver_name: Optional[str] = None,
    approver_email: Optional[str] = None,
    default_password: str = "nimda"
) -> str:
    """
    Scaffolds a complete, realistic B2B organization hierarchy with units, cost centers, budgets, permissions, and demo users.
    """
    return _b2b.scaffold_org(
        root_unit_id=root_unit_id,
        root_unit_name=root_unit_name,
        sub_units=sub_units,
        currency=currency,
        languages=languages,
        monthly_budget=monthly_budget,
        approval_threshold=approval_threshold,
        buyer_name=buyer_name,
        buyer_email=buyer_email,
        approver_name=approver_name,
        approver_email=approver_email,
        default_password=default_password
    )

@mcp.tool()
def hac_b2b_org_doctor(user_uid: str, lang: str = "zh") -> str:
    """
    Diagnoses a B2B user's organizational context (Unit, Cost Center, Budget, Approvers, Permissions) with language-aligned output.
    """
    return _b2b.diagnose_user_org(user_uid=user_uid, lang=lang)

@mcp.tool()
def hac_solr_reindex(
    config_name: Optional[str] = None,
    mode: str = "FULL"
) -> str:
    """
    Triggers an immediate in-process Solr index build (FULL or UPDATE) bypassing cronjob queue delays.
    """
    return _solr_sync.solr_reindex(config_name=config_name, mode=mode)

@mcp.tool()
def hac_solr_status() -> str:
    """
    Queries Solr search configurations and recent indexer cronjobs.
    """
    return _solr_sync.solr_status()

@mcp.tool()
def hac_catalog_sync(
    catalog_id: str,
    source_version: str = "Staged",
    target_version: str = "Online"
) -> str:
    """
    Triggers synchronization from source catalog version to target catalog version.
    """
    return _solr_sync.catalog_sync(catalog_id=catalog_id, source_version=source_version, target_version=target_version)

@mcp.tool()
def hac_cache_clear() -> str:
    """
    Clears the Hybris Region Cache in real time to ensure modified data and CMS pages reflect immediately.
    """
    return _solr_sync.cache_clear()

@mcp.tool()
def hac_check_i18n_completeness(
    item_type: str = "Product",
    catalog_id: Optional[str] = None,
    languages: Optional[List[str]] = None
) -> str:
    """
    Scans for missing localized names/descriptions in target languages.
    """
    return _solr_sync.check_i18n_completeness(item_type=item_type, catalog_id=catalog_id, languages=languages)

@mcp.tool()
def hac_ingest_external_storefront(
    site_url: str,
    catalog_id: str,
    max_products: int = 20,
    convert_to_b2b_cases: bool = False,
    target_currency: str = "USD",
    sync_online: bool = True,
    reindex_solr: bool = True
) -> str:
    """
    Crawls an external storefront, normalizes products, generates and imports ImpEx, syncs online, and reindexes Solr.
    """
    return _crawler.ingest_to_hybris(
        site_url=site_url,
        catalog_id=catalog_id,
        max_products=max_products,
        convert_to_b2b_cases=convert_to_b2b_cases,
        target_currency=target_currency,
        sync_online=sync_online,
        reindex_solr=reindex_solr
    )

# --- 统一脚本库与自完善新工具 ---

@mcp.tool()
def hac_library_list(
    script_type: Optional[str] = None,
    category: Optional[str] = None,
    client: Optional[str] = None,
    query: Optional[str] = None
) -> str:
    """
    Lists and searches verified successful scripts (ImpEx and Groovy) stored in the unified script library.
    
    Args:
        script_type: Filter by 'impex' or 'groovy' (optional)
        category: Filter by category (e.g. 'b2b_organization', 'search_solr', 'cache_ops')
        client: Filter by customer/client name (optional)
        query: Search keyword across script names, tags, descriptions (optional)
    """
    items = _script_mgr.list_scripts(script_type=script_type, category=category, client=client, query=query)
    if not items:
        return "📁 脚本库中暂无匹配的已归档脚本。"

    out = [f"📁 **=== hybris-hac 统一脚本资产库 (共检索到 {len(items)} 个已验证脚本) ===**\n"]
    for it in items:
        out.append(f"- **`{it['id']}`** [{it['type'].upper()}] - {it['name']}")
        out.append(f"  • **适用场景/分类:** `{it['category']}` | **客户:** {it.get('client', '通用')}")
        out.append(f"  • **行数:** {it['line_count']} 行 | **归档时间:** {it['created_at'][:19]}")
        out.append(f"  • **描述:** {it.get('description', '无')}")
        out.append(f"  • **物理路径:** `{it['path']}`\n")
    return "\n".join(out)

@mcp.tool()
def hac_library_get(script_id: str) -> str:
    """
    Retrieves the complete content and metadata of a verified script from the unified script library.
    
    Args:
        script_id: Unique identifier of the script (e.g. 'impex_20260911_115440_b2b_org_medical_mindray')
    """
    entry = _script_mgr.get_script_by_id(script_id)
    if not entry:
        return f"❌ 未在脚本库中找到 ID 为 '{script_id}' 的脚本。"
    
    out = [
        f"📄 **脚本详情: {entry['name']} ({entry['type'].upper()})**",
        f"- **ID:** `{entry['id']}`",
        f"- **客户:** {entry.get('client', '通用')}",
        f"- **分类:** `{entry['category']}`",
        f"- **路径:** `{entry['path']}`",
        f"- **内容预览:**",
        f"```{entry['type']}",
        entry.get("content", ""),
        "```"
    ]
    return "\n".join(out)

@mcp.tool()
def hac_self_improve(
    target_file: str,
    description: str,
    updated_code: str
) -> str:
    """
    Self-evolves the MCP by updating one of its own Python modules.
    Automatically creates a backup, runs syntax checks and full regression test suite.
    Rolls back immediately if tests fail.
    
    Args:
        target_file: Relative filename within MCP directory (e.g. 'site_scaffolder.py', 'b2b_org_helper.py')
        description: Summary of the improvement, fix, or capability being added
        updated_code: Complete updated Python code for the target module
    """
    return _self_improver.apply_improvement(
        target_file=target_file,
        improvement_description=description,
        new_file_content=updated_code
    )

@mcp.tool()
def hac_self_diagnose() -> str:
    """
    Runs a self-health audit on the hybris-hac MCP server: checks regression test suite,
    counts archived scripts in unified library, and reviews learned best-practice rules.
    """
    return _self_improver.diagnose_self()

@mcp.tool()
def hac_record_learning(
    pattern_name: str,
    problem: str,
    solution: str,
    tags: Optional[List[str]] = None
) -> str:
    """
    Records a newly discovered error pattern, solution, or best practice into the MCP's persistent knowledge base.
    
    Args:
        pattern_name: Short title for the rule/pattern (e.g. 'B2BCostCenter Type Code')
        problem: Description of the obstacle, error, or symptom encountered
        solution: Exact fix, workaround, or ImpEx/Groovy snippet that solves it
        tags: Categorization tags (e.g. ['b2b', 'impex'])
    """
    return _self_improver.record_learning(
        pattern_name=pattern_name,
        problem=problem,
        solution=solution,
        tags=tags
    )

@mcp.tool()
def hac_promotion_scaffold(
    rule_code: str,
    name: str,
    promo_type: str = "ORDER_THRESHOLD_DISCOUNT",
    description: Optional[str] = None,
    threshold_amount: Optional[float] = None,
    currency: str = "USD",
    discount_amount: Optional[float] = None,
    discount_percentage: Optional[float] = None,
    qualifying_products: Optional[List[str]] = None,
    gift_product: Optional[str] = None,
    gift_quantity: int = 1,
    target_rule_code: Optional[str] = None,
    message_fired: Optional[str] = None,
    promo_group: str = "powertoolsPromoGrp",
    priority: int = 150,
    compile_immediately: bool = True,
    lang: str = "zh"
) -> str:
    """
    Scaffolds, configures, and publishes a PromotionSourceRule in the SAP Commerce Drools Rule Engine.
    
    Args:
        rule_code: Unique code for the promotion rule (e.g. 'promo_summer_sale_100')
        name: Business title/name of the promotion
        promo_type: Promotion pattern:
            - 'ORDER_THRESHOLD_DISCOUNT': Order threshold discount (spend X get fixed discount or percentage off)
            - 'ORDER_THRESHOLD_FREE_GIFT': Spend X get free gift SKU
            - 'BUNDLE_FREE_GIFT': Multi-product bundle (A+B+C) gets free gift
            - 'PRODUCT_DISCOUNT': Specific product percentage or fixed discount
            - 'POTENTIAL_MESSAGE': Upsell hint when cart has not reached threshold
        threshold_amount: Minimum cart total threshold (e.g. 500.0)
        currency: Currency code (e.g. 'USD', 'CNY', 'HKD', 'EUR')
        discount_amount: Fixed discount amount (e.g. 50.0)
        discount_percentage: Percentage discount (e.g. 10.0 for 10% off)
        qualifying_products: List of qualifying product codes (SKUs)
        gift_product: SKU of the free gift product
        gift_quantity: Quantity of the free gift product (default 1)
        target_rule_code: Target rule code to check execution for POTENTIAL_MESSAGE
        message_fired: User notification message when promotion executes
        promo_group: Target PromotionGroup identifier (default 'powertoolsPromoGrp')
        priority: Rule execution priority (default 150)
        compile_immediately: If True, triggers Drools rules-module compilation immediately (default True)
        lang: Output language ('zh' for Chinese, 'en' for English)
    """
    return _promo.scaffold_promotion(
        rule_code=rule_code,
        name=name,
        description=description,
        promo_type=promo_type,
        threshold_amount=threshold_amount,
        currency=currency,
        discount_amount=discount_amount,
        discount_percentage=discount_percentage,
        qualifying_products=qualifying_products,
        gift_product=gift_product,
        gift_quantity=gift_quantity,
        target_rule_code=target_rule_code,
        message_fired=message_fired,
        promo_group=promo_group,
        priority=priority,
        compile_immediately=compile_immediately,
        lang=lang
    )

@mcp.tool()
def hac_promotion_list(
    promo_group: Optional[str] = None,
    status: Optional[str] = None,
    lang: str = "zh"
) -> str:
    """
    Lists and monitors active and draft PromotionSourceRules in SAP Commerce Cloud.
    
    Args:
        promo_group: Filter by PromotionGroup identifier (optional)
        status: Filter by status ('PUBLISHED', 'UNPUBLISHED', 'MODIFIED', 'ALL')
        lang: Output language ('zh' or 'en')
    """
    return _promo.list_promotions(
        promo_group=promo_group,
        status=status,
        lang=lang
    )

@mcp.tool()
def hac_storefront_cms_scaffold(
    content_catalog: str = "powertools-spaContentCatalog",
    product_catalog: str = "powertoolsProductCatalog",
    hero_title: Optional[str] = None,
    featured_products: Optional[List[str]] = None,
    bestseller_products: Optional[List[str]] = None,
    banner_configs: Optional[List[Dict[str, str]]] = None,
    sync_online: bool = True,
    clear_cache: bool = True,
    lang: str = "zh"
) -> str:
    """
    Scaffolds, customizes, and publishes CMS layout components for Composable Storefront (Spartacus).
    
    Args:
        content_catalog: Target CMS Content Catalog (default 'powertools-spaContentCatalog')
        product_catalog: Target Product Catalog (default 'powertoolsProductCatalog')
        hero_title: Title text for the Hero announcement
        featured_products: List of product SKUs for the 'What's New' product carousel
        bestseller_products: List of product SKUs for the 'Bestsellers' product carousel
        banner_configs: List of banner dicts, each with 'uid', 'imageUrl', and optional 'urlLink'
        sync_online: If True, triggers synchronization from Staged to Online catalog (default True)
        clear_cache: If True, flushes Region Cache so changes reflect on storefront immediately (default True)
        lang: Output language ('zh' or 'en')
    """
    return _storefront.scaffold_storefront_cms(
        content_catalog=content_catalog,
        product_catalog=product_catalog,
        hero_title=hero_title,
        featured_products=featured_products,
        bestseller_products=bestseller_products,
        banner_configs=banner_configs,
        sync_online=sync_online,
        clear_cache=clear_cache,
        lang=lang
    )

@mcp.tool()
def hac_storefront_autofix(
    site_id: str = "powertools-spa",
    storefront_url: str = "http://localhost:4200",
    lang: str = "zh"
) -> str:
    """
    One-click automated repair for Composable Storefront (Spartacus) headless readiness issues:
    - Injects matching frontend origin regex into BaseSite.urlPatterns
    - Dynamically permits frontend origin in CORS (corsfilter.commercewebservices.allowedOrigins)
    - Verifies OAuth2 client credentials
    - Flushes Region Cache for real-time frontend routing
    
    Args:
        site_id: Target BaseSite UID (e.g. 'powertools-spa')
        storefront_url: Frontend URL Origin (e.g. 'http://localhost:4200' or 'https://localhost:4200')
        lang: Output language ('zh' or 'en')
    """
    return _storefront.autofix_headless_readiness(
        site_id=site_id,
        storefront_url=storefront_url,
        lang=lang
    )

@mcp.tool()
def hac_storefront_app_config(
    storefront_dir: str = "/Users/I319510/sap-ai-commerce-demo/spartacus-storefront",
    backend_url: str = "https://localhost:9002",
    base_site: str = "powertools-spa",
    b2b_mode: bool = True,
    lang: str = "zh"
) -> str:
    """
    Inspects and aligns the local Composable Storefront Angular workspace configuration:
    - Synchronizes backend OCC CX_BASE_URL in .env-cmdrc
    - Aligns baseSite and multi-language routing in spartacus-b2b-configuration.providers.ts
    - Verifies B2B/B2C mode flags
    
    Args:
        storefront_dir: Path to local Spartacus storefront repository
        backend_url: Target Commerce Cloud backend OCC URL (default 'https://localhost:9002')
        base_site: Target BaseSite UID (default 'powertools-spa')
        b2b_mode: Whether B2B mode is enabled (default True)
        lang: Output language ('zh' or 'en')
    """
    return _storefront.configure_local_storefront_app(
        storefront_dir=storefront_dir,
        backend_url=backend_url,
        base_site=base_site,
        b2b_mode=b2b_mode,
        lang=lang
    )

if __name__ == "__main__":
    # Run the server over stdio
    mcp.run(transport="stdio")
