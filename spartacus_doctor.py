from typing import Optional, Dict, Any

class SpartacusDoctor:
    def __init__(self, client):
        self.client = client

    def diagnose(self, site_id: str = "powertools-spa", storefront_url: str = "http://localhost:4200", lang: str = "zh") -> str:
        """
        Performs a full headless readiness health check for a Spartacus storefront and BaseSite,
        with language-aligned diagnostic output (Chinese or English).
        """
        origin = storefront_url.rstrip("/")

        groovy_script = f"""
import de.hybris.platform.site.BaseSiteService
import de.hybris.platform.basecommerce.model.site.BaseSiteModel
import de.hybris.platform.store.BaseStoreModel
import de.hybris.platform.cms2.model.contents.ContentCatalogModel
import de.hybris.platform.cms2.model.pages.AbstractPageModel
import de.hybris.platform.util.Config
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def siteId = "{site_id}"
def origin = "{origin}"
def isZh = "{lang}".toLowerCase().startsWith("zh")

if (isZh) {{
    println "🩺 === Spartacus 无头商城就绪度深度体检: [${{siteId}}] ==="
    println "🎯 目标前端 Origin: ${{origin}}\\n"
}} else {{
    println "🩺 === Spartacus Headless Doctor for BaseSite: [${{siteId}}] ==="
    println "🎯 Target Storefront Origin: ${{origin}}\\n"
}}

// 1. BaseSite Check
def siteQuery = new FlexibleSearchQuery("SELECT {{pk}} FROM {{BaseSite}} WHERE {{uid}}=?uid")
siteQuery.addQueryParameter("uid", siteId)
def sites = flexibleSearchService.search(siteQuery).result
if (!sites) {{
    if (isZh) {{
        println "❌ [BaseSite] Commerce Cloud 中未检索到站点 '${{siteId}}'！"
        println "   修复建议: 请通过 ImpEx 创建该站点或指定已存在的 siteId。"
    }} else {{
        println "❌ [BaseSite] Site '${{siteId}}' NOT found in Commerce Cloud!"
        println "   Recommendation: Create BaseSite via ImpEx or specify an existing siteId."
    }}
    return
}}

BaseSiteModel site = sites[0]
def defCurr = site.stores ? site.stores[0].defaultCurrency?.isocode : 'N/A'
if (isZh) {{
    println "✅ [BaseSite] 已就绪: ${{site.uid}} | 业务渠道: ${{site.channel}} | 默认语言: ${{site.defaultLanguage?.isocode}} | 默认币种: ${{defCurr}}"
}} else {{
    println "✅ [BaseSite] Found: ${{site.uid}} | Channel: ${{site.channel}} | Default Lang: ${{site.defaultLanguage?.isocode}} | Default Curr: ${{defCurr}}"
}}

// 2. URL Pattern Check
def patterns = site.urlPatterns ?: []
def urlWithSlash = origin + "/"
def matchedPattern = patterns.find {{ origin.matches(it) || urlWithSlash.matches(it) }}
if (matchedPattern) {{
    println isZh ? "✅ [URL Pattern] 成功匹配前端正则规则: ${{matchedPattern}}" : "✅ [URL Pattern] Matched: ${{matchedPattern}}"
}} else {{
    if (isZh) {{
        println "⚠️ [URL Pattern] 警告: BaseSite 未配置匹配 '${{origin}}' 的正则规则！"
        println "   排查风险: Spartacus 前台请求 OCC API 时将因站点不匹配被拒绝路由。"
        println "   修复建议: 向 BaseSite.urlPatterns 追加当前前端地址正则。"
    }} else {{
        println "⚠️ [URL Pattern] No pattern in BaseSite matches '${{origin}}'!"
        println "   Recommendation: Add regex to BaseSite.urlPatterns to match your storefront host and port."
    }}
}}

// 3. CORS Check
def corsAllowed = Config.getParameter("corsfilter.commercewebservices.allowedOrigins") ?: ""
if (corsAllowed.contains(origin) || corsAllowed.contains("*")) {{
    println isZh ? "✅ [CORS 跨域] allowedOrigins 已包含目标前端: ${{origin}}" : "✅ [CORS Filter] Allowed origin contains: ${{origin}}"
}} else {{
    if (isZh) {{
        println "⚠️ [CORS 跨域] 'corsfilter.commercewebservices.allowedOrigins' 缺少: ${{origin}}"
        println "   排查风险: 浏览器控制台将报 CORS header 拦截错误。"
        println "   修复建议: 在 local.properties 中追加 '${{origin}}' 并重启或热更新配置。"
    }} else {{
        println "⚠️ [CORS Filter] 'corsfilter.commercewebservices.allowedOrigins' missing: ${{origin}}"
        println "   Recommendation: Add '${{origin}}' to local.properties or hac project.properties."
    }}
}}

// 4. OAuth Client Check
def oauthQuery = new FlexibleSearchQuery("SELECT {{pk}} FROM {{OAuthClientDetails}}")
def oauthClients = flexibleSearchService.search(oauthQuery).result*.clientId
def trusted = ["mobile_android", "client-side", "spartacus-client"]
def foundTrusted = oauthClients.findAll {{ it in trusted }}
if (foundTrusted) {{
    println isZh ? "✅ [OAuth 凭据] 找到受信任的客户端: " + foundTrusted.join(", ") : "✅ [OAuth Client] Trusted client(s) found: " + foundTrusted.join(", ")
}} else {{
    println isZh ? "⚠️ [OAuth 凭据] 未检测到标准 Spartacus 客户端 ('mobile_android')，前台用户登录认证可能失败！" : "⚠️ [OAuth Client] No standard Spartacus client ('mobile_android') found in OAuthClientDetails!"
}}

// 5. Stores & Catalogs
if (site.stores) {{
    site.stores.each {{ BaseStoreModel store ->
        def prods = store.catalogs*.id.join(", ")
        println isZh ? "✅ [BaseStore] 关联店铺: ${{store.uid}} (挂载商品目录: ${{prods ?: '无'}})" : "✅ [BaseStore] Linked: ${{store.uid}} (Product Catalogs: ${{prods ?: 'None'}})"
    }}
}} else {{
    println isZh ? "❌ [BaseStore] BaseSite 未关联任何 BaseStore 店铺！" : "❌ [BaseStore] BaseSite has NO linked BaseStore!"
}}

// 6. CMS Online Content Catalog & Homepage Check
def cmsCatalogs = site.contentCatalogs ?: []
if (!cmsCatalogs) {{
    def cmsQuery = new FlexibleSearchQuery("SELECT {{pk}} FROM {{ContentCatalog}}")
    cmsCatalogs = flexibleSearchService.search(cmsQuery).result.findAll {{
        it.id.startsWith(siteId) || siteId.startsWith(it.id.replace("-spa", "").replace("ContentCatalog", ""))
    }}
}}

if (cmsCatalogs) {{
    cmsCatalogs.each {{ cat ->
        def pageQuery = new FlexibleSearchQuery("SELECT {{p.pk}} FROM {{AbstractPage AS p JOIN CatalogVersion AS cv ON {{p.catalogVersion}}={{cv.pk}}}} WHERE {{cv.catalog}}=?cat AND {{cv.version}}='Online'")
        pageQuery.addQueryParameter("cat", cat)
        def pages = flexibleSearchService.search(pageQuery).result
        def home = pages.find {{ it.uid?.toLowerCase()?.contains("home") }}
        if (home) {{
            println isZh ? "✅ [CMS 首页] Online 首页正常就绪: '${{home.uid}}' (已发布总页面数: ${{pages.size()}})" : "✅ [CMS Homepage] Online Homepage found: '${{home.uid}}' (Total online pages: ${{pages.size()}})"
        }} else {{
            println isZh ? "⚠️ [CMS 首页] ${{cat.id}}:Online 中未找到 Homepage，Spartacus 访问根路由 '/' 时将 404！" : "⚠️ [CMS Homepage] No Online Homepage found in ${{cat.id}}:Online (Total online pages: ${{pages.size()}})"
        }}
    }}
}} else {{
    println isZh ? "⚠️ [CMS 内容目录] BaseSite 未绑定任何 ContentCatalog！" : "⚠️ [CMS Catalog] No ContentCatalog linked to BaseSite!"
}}

println isZh ? "\\n🩺 体检全部完成！" : "\\n🩺 Diagnosis complete!"
"""
        res = self.client.execute_groovy(script=groovy_script, commit=False)
        out = res.get("outputText", "").strip()
        stack = res.get("stacktraceText", "").strip()
        if stack:
            return f"{out}\n\n⚠️ Error during diagnosis:\n{stack}" if out else stack
        return out
