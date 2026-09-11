import json
import re
from typing import Optional, List, Dict, Any

class SiteScaffolder:
    def __init__(self, client):
        self.client = client

    def scaffold_site(
        self,
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
    ) -> Dict[str, Any]:
        channel_upper = channel.upper()
        is_b2b = channel_upper == "B2B"

        langs = languages or (["en", "zh"] if not is_b2b else ["en", "zh_CN", "zh_TW"])
        default_lang = langs[0]
        site_id = re.sub(r"[^a-zA-Z0-9_-]", "-", site_id.strip())
        store_id = f"{site_id}-store"
        prod_cat_id = f"{site_id}ProductCatalog"

        # Multi-Brand Enterprise Architecture:
        # 1. Base template catalog provides all 130+ shared SPA pages (Cart, Checkout, PDP, etc.)
        base_template_cc = "powertools-spaContentCatalog" if is_b2b else "electronics-spaContentCatalog"

        # 2. Each brand gets its own dedicated ContentCatalog for Homepage, Banners, Navigation
        brand_cc = content_catalog or f"{site_id}-spaContentCatalog"

        # Register brand_cc first, then base_template_cc for fallback
        if brand_cc == base_template_cc:
            assigned_ccs = [brand_cc]
        else:
            assigned_ccs = [brand_cc, base_template_cc]

        countries = delivery_countries or ["US", "CN", "GB", "DE", "HK", "JP", "FR", "SG"]
        countries_str = ",".join(countries)

        origin_clean = storefront_origin.rstrip("/")
        escaped_origin = origin_clean.replace(".", r"\.").replace(":", r"\:")
        url_patterns = [
            f"(?i)^https?://[^/]+(/[^?]*)?\\?(.*\\&)?(site={site_id})(|\\&.*)$",
            f"(?i)^https?://{site_id}\\.[^/]+(|/.*|\\?.*)$",
            f"(?i)^{escaped_origin}(|/.*|\\?.*|#.*)$",
            f"(?i)^https?://localhost(:[\\d]+)?/.*$"
        ]

        # Non-destructive pre-check: only create currency if it does not exist
        curr_query = f"SELECT {{pk}} FROM {{Currency}} WHERE {{isocode}}='{currency}'"
        curr_exists = bool(self.client.execute_flexsearch(curr_query).get("resultList"))

        # Non-destructive pre-check: only create OAuth clients if missing
        oauth_missing = []
        for cid in ["mobile_android", "spartacus-client"]:
            oq = f"SELECT {{pk}} FROM {{OAuthClientDetails}} WHERE {{clientId}}='{cid}'"
            if not self.client.execute_flexsearch(oq).get("resultList"):
                oauth_missing.append(cid)

        impex_lines = [
            "# ====================================================================",
            f"# Greenfield Site Scaffolding: {site_name} ({site_id})",
            f"# Channel: {channel_upper} | Currency: {currency} | Store: {store_id}",
            "# ====================================================================",
            f"$siteUid = {site_id}",
            f"$storeUid = {store_id}",
            f"$prodCatalog = {prod_cat_id}",
            f"$curr = {currency}",
            f"$defaultLang = {default_lang}",
            "",
        ]

        if not curr_exists:
            impex_lines.extend([
                "# 1. Ensure Currency exists (created because not found in system)",
                "INSERT_UPDATE Currency;isocode[unique=true];conversion;digits;symbol",
                f";{currency};1.0;2;{currency}",
                ""
            ])
        else:
            impex_lines.append(f"# [Safety Guard] Currency '{currency}' already exists in system, preserving existing exchange rates.")

        impex_lines.append("INSERT_UPDATE Language;isocode[unique=true];active[default=true]")
        for l in langs:
            impex_lines.append(f";{l};true")

        impex_lines.extend([
            "",
            "# 2. Product Catalog and Versions",
            "INSERT_UPDATE Catalog;id[unique=true];name[lang=en]",
            f";$prodCatalog;{site_name} Product Catalog",
            "",
            "INSERT_UPDATE CatalogVersion;catalog(id)[unique=true];version[unique=true];active;defaultCatalog;readPrincipals(uid)",
            ";$prodCatalog;Staged;false;false;employeegroup",
            ";$prodCatalog;Online;true;true;customergroup",
            "",
            "# 3. Catalog Sync Job (Staged -> Online)",
            "INSERT_UPDATE CatalogVersionSyncJob;code[unique=true];sourceVersion(catalog(id),version);targetVersion(catalog(id),version);targetVersionCatalog(id);targetVersionVersion;active[default=true]",
            f";sync_$prodCatalog;$prodCatalog:Staged;$prodCatalog:Online;$prodCatalog;Online;true",
        ])

        # 3b. Ensure Brand Dedicated Content Catalog exists if not base template
        known_catalogs = ["powertools-spaContentCatalog", "electronics-spaContentCatalog", "powertoolsContentCatalog", "electronicsContentCatalog", "apparel-uk-spaContentCatalog"]
        if brand_cc not in known_catalogs:
            impex_lines.extend([
                "",
                "# 3b. Brand Dedicated Content Catalog (Homepage, Banners, Nav)",
                "INSERT_UPDATE ContentCatalog;id[unique=true];name[lang=en]",
                f";{brand_cc};{site_name} Brand Content Catalog",
                "",
                "INSERT_UPDATE CatalogVersion;catalog(id)[unique=true];version[unique=true];active;defaultCatalog;readPrincipals(uid)",
                f";{brand_cc};Staged;false;false;employeegroup",
                f";{brand_cc};Online;true;true;customergroup",
                "",
                "INSERT_UPDATE CatalogVersionSyncJob;code[unique=true];sourceVersion(catalog(id),version);targetVersion(catalog(id),version);targetVersionCatalog(id);targetVersionVersion;active[default=true]",
                f";sync_{brand_cc};{brand_cc}:Staged;{brand_cc}:Online;{brand_cc};Online;true",
            ])

        impex_lines.extend([
            "",
            "# 4. BaseStore",
            "INSERT_UPDATE BaseStore;uid[unique=true];catalogs(id);currencies(isocode);net;taxGroup(code);languages(isocode);defaultCurrency(isocode);defaultLanguage(isocode);deliveryCountries(isocode);name[lang=en]",
            f";$storeUid;$prodCatalog;{currency};{"true" if is_b2b else "false"};us-taxes;{",".join(langs)};{currency};{default_lang};{countries_str};{site_name} Store",
            "",
            "# 5. CMSSite (BaseSite) - Layered Content Catalogs: Brand-specific first, Template fallback second",
            "INSERT_UPDATE CMSSite;uid[unique=true];stores(uid);contentCatalogs(id);defaultLanguage(isocode);channel(code);urlPatterns;active[default=true]",
            f";$siteUid;$storeUid;{','.join(assigned_ccs)};{default_lang};{channel_upper};{','.join(url_patterns)};true",
        ])

        if oauth_missing:
            impex_lines.extend([
                "",
                "# 6. Headless OAuth Client Verification (only creating missing clients)",
                "INSERT_UPDATE OAuthClientDetails;clientId[unique=true];resourceIds;scope;authorizedGrantTypes;authorities;clientSecret"
            ])
            for mc in oauth_missing:
                impex_lines.append(f";{mc};hybris;basic;authorization_code,refresh_token,password,client_credentials;ROLE_CLIENT;nimda")
        else:
            impex_lines.extend([
                "",
                "# 6. [Safety Guard] OAuth clients already verified and present, leaving credentials untouched."
            ])

        impex_script = "\n".join(impex_lines)
        impex_res = self.client.import_impex(script_content=impex_script)

        b2b_res_text = None
        if is_b2b and setup_b2b_org:
            from b2b_org_helper import B2BOrgHelper
            b2b_helper = B2BOrgHelper(self.client)
            b2b_root_id = f"{site_id.upper().replace('-', '_')}_HQ"
            b2b_res_text = b2b_helper.scaffold_org(
                root_unit_id=b2b_root_id,
                root_unit_name=site_name,
                currency=currency,
                languages=langs,
                monthly_budget=monthly_budget,
                approval_threshold=approval_threshold
            )

        spartacus_config = f"""// spartacus-configuration.module.ts
provideConfig(<OccConfig>{{
  backend: {{
    occ: {{
      baseUrl: '{self.client.base_url}',
      prefix: '/occ/v2/'
    }}
  }}
}}),
provideConfig(<SiteContextConfig>{{
  context: {{
    baseSite: ['{site_id}'],
    language: {json.dumps(langs)},
    currency: ['{currency}']
  }}
}})"""

        return {
            "site_id": site_id,
            "site_name": site_name,
            "channel": channel_upper,
            "product_catalog": prod_cat_id,
            "base_store": store_id,
            "content_catalogs": assigned_ccs,
            "brand_content_catalog": brand_cc,
            "fallback_content_catalog": base_template_cc,
            "impex_status": impex_res.get("status", "UNKNOWN"),
            "impex_message": impex_res.get("message", ""),
            "b2b_scaffold": b2b_res_text,
            "spartacus_config": spartacus_config
        }

    def list_sites(self, lang: str = "zh") -> str:
        """
        Lists all CMSSites in the SAP Commerce instance with their BaseStore,
        ProductCatalog, ContentCatalogs, Languages, Currencies, and active status.
        Essential for enterprise multi-brand group governance.
        """
        is_zh = lang.startswith("zh")
        groovy_script = """
import de.hybris.platform.cms2.model.site.CMSSiteModel
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def fss = spring.getBean("flexibleSearchService")
def sites = fss.search(new FlexibleSearchQuery("SELECT {pk} FROM {CMSSite}")).result

def table = []
sites.each { s ->
    def stores = s.stores ? s.stores.collect { it.uid }.join(", ") : "-"
    def ccs = s.contentCatalogs ? s.contentCatalogs.collect { it.id }.join(", ") : "-"
    def langs = s.defaultLanguage ? s.defaultLanguage.isocode : "-"
    def curr = (s.stores && s.stores[0].defaultCurrency) ? s.stores[0].defaultCurrency.isocode : "-"
    table.add("| `" + s.uid + "` | " + (s.name ?: s.uid) + " | " + (s.channel?.code ?: '-') + " | `" + stores + "` | `" + ccs + "` | " + langs + " / " + curr + " | " + (s.active ? '🟢 激活' : '⚪ 禁用') + " |")
}

table.join("\\n")
"""
        try:
            res = self.client.execute_groovy(groovy_script)
            rows = (res.get("executionResult", "") or res.get("outputText", "")).strip()
            
            title = "🏢 **=== SAP Commerce 集团多品牌与多站点概览 ===**" if is_zh else "🏢 **=== SAP Commerce Multi-Brand Sites Overview ===**"
            headers = """| 站点 UID (BaseSite) | 站点名称 (Brand Name) | 业务渠道 | 关联店铺 (BaseStore) | 绑定内容目录 (ContentCatalogs) | 默认语言/币种 | 运行状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |""" if is_zh else """| Site UID | Brand Name | Channel | BaseStore | ContentCatalogs | Default Lang / Curr | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"""

            return f"{title}\n\n{headers}\n{rows}\n\n💡 *提示：每个品牌站点均支持独立的商品主数据、私有首页/Banner与通用结算流程分层继承。*"
        except Exception as e:
            return f"❌ 查询站点列表失败: {e}"
