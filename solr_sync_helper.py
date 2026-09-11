import json
from typing import Optional, List, Dict, Any

class SolrSyncHelper:
    def __init__(self, client):
        self.client = client

    def solr_reindex(self, config_name: Optional[str] = None, mode: str = "FULL") -> str:
        """
        Triggers a Solr reindex (FULL or UPDATE) on SolrFacetSearchConfig.
        """
        mode_upper = mode.upper()
        method_name = "performFullIndex" if mode_upper == "FULL" else "performUpdateIndex"

        groovy_script = f"""
import de.hybris.platform.solrfacetsearch.config.FacetSearchConfig
import de.hybris.platform.solrfacetsearch.model.config.SolrFacetSearchConfigModel
import de.hybris.platform.solrfacetsearch.config.FacetSearchConfigService
import de.hybris.platform.solrfacetsearch.indexer.IndexerService
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def indexerService = spring.getBean("indexerService", IndexerService.class)
def facetConfigService = spring.getBean("facetSearchConfigService", FacetSearchConfigService.class)

def fsq
if ("{config_name or ''}") {{
    fsq = new FlexibleSearchQuery("SELECT {{pk}} FROM {{SolrFacetSearchConfig}} WHERE {{name}}=?name")
    fsq.addQueryParameter("name", "{config_name or ''}")
}} else {{
    fsq = new FlexibleSearchQuery("SELECT {{pk}} FROM {{SolrFacetSearchConfig}}")
}}
def configs = flexibleSearchService.search(fsq).result

if (!configs) {{
    println "❌ No SolrFacetSearchConfig found matching: {config_name or 'ALL'}"
    return
}}

println "=== Starting Solr {mode_upper} Index (${{configs.size()}} configurations) ==="
configs.each {{ SolrFacetSearchConfigModel cfgModel ->
    def name = cfgModel.getName()
    def start = System.currentTimeMillis()
    try {{
        FacetSearchConfig cfg = facetConfigService.getConfiguration(name)
        def types = cfg.getIndexConfig().getIndexedTypes().values()*.getIndexName()
        indexerService.{method_name}(cfg)
        def elapsed = System.currentTimeMillis() - start
        println "✅ [${{name}}] {mode_upper} index completed in ${{elapsed}}ms (Types: ${{types.join(', ')}})"
    }} catch (Exception e) {{
        println "❌ [${{name}}] Failed: ${{e.class.simpleName}}: ${{e.message}}"
    }}
}}
"""
        res = self.client.execute_groovy(script=groovy_script, commit=True)
        return res.get("outputText", "").strip() or res.get("stacktraceText", "")

    def solr_status(self) -> str:
        """
        Queries Solr search configurations and recent indexer cronjobs.
        """
        groovy_script = """
import de.hybris.platform.solrfacetsearch.model.config.SolrFacetSearchConfigModel
import de.hybris.platform.solrfacetsearch.model.indexer.cron.SolrIndexerCronJobModel
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

println "=== Solr Facet Search Configurations ==="
def cfgQuery = new FlexibleSearchQuery("SELECT {pk} FROM {SolrFacetSearchConfig}")
def configs = flexibleSearchService.search(cfgQuery).result
configs.each { SolrFacetSearchConfigModel c ->
    println "Config: ${c.name} | Server: ${c.solrServerConfig?.name} | Mode: ${c.solrServerConfig?.mode}"
}

println "\\n=== Recent Solr Indexer CronJobs ==="
def cjQuery = new FlexibleSearchQuery("SELECT {pk} FROM {SolrIndexerCronJob} ORDER BY {modifiedtime} DESC")
cjQuery.setCount(8)
def jobs = flexibleSearchService.search(cjQuery).result
jobs.each { SolrIndexerCronJobModel j ->
    println "Job: ${j.code} | Status: ${j.status} | Result: ${j.result} | Config: ${j.facetSearchConfig?.name} | Finished: ${j.endTime ?: j.startTime}"
}
"""
        res = self.client.execute_groovy(script=groovy_script, commit=False)
        return res.get("outputText", "").strip() or res.get("stacktraceText", "")

    def catalog_sync(self, catalog_id: str, source_version: str = "Staged", target_version: str = "Online") -> str:
        """
        Triggers synchronization from source catalog version to target catalog version.
        """
        groovy_script = f"""
import de.hybris.platform.catalog.CatalogVersionService
import de.hybris.platform.catalog.synchronization.CatalogSynchronizationService
import de.hybris.platform.catalog.model.synchronization.CatalogVersionSyncJobModel
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def cvService = spring.getBean("catalogVersionService", CatalogVersionService)
def syncJobService = spring.getBean("catalogSynchronizationService", CatalogSynchronizationService)

def src = cvService.getCatalogVersion("{catalog_id}", "{source_version}")
def tgt = cvService.getCatalogVersion("{catalog_id}", "{target_version}")

if (!src || !tgt) {{
    println "❌ CatalogVersion not found for {catalog_id}:{source_version} or {target_version}"
    return
}}

def syncJob = syncJobService.getSyncJob(src, tgt)
if (!syncJob) {{
    println "❌ No CatalogVersionSyncJob found for {catalog_id}:{source_version} -> {target_version}"
    return
}}

println "▶ Starting Catalog Sync Job: ${{syncJob.code}}..."
def syncCronJob = syncJobService.createSyncCronJob(syncJob)
syncJobService.performSynchronization(syncCronJob)
println "✅ Sync launched: ${{syncCronJob.code}} | Status: ${{syncCronJob.status}} | Result: ${{syncCronJob.result}}"
"""
        res = self.client.execute_groovy(script=groovy_script, commit=True)
        return res.get("outputText", "").strip() or res.get("stacktraceText", "")

    def cache_clear(self) -> str:
        """
        Clears the Hybris Region Cache.
        """
        groovy_script = """
import de.hybris.platform.core.Registry

def cache = Registry.getCurrentTenant().getCache()
cache.clear()
println "✅ Hybris Region Cache cleared successfully!"
"""
        res = self.client.execute_groovy(script=groovy_script, commit=True)
        return res.get("outputText", "").strip() or res.get("stacktraceText", "")

    def check_i18n_completeness(self, item_type: str = "Product", catalog_id: Optional[str] = None, languages: Optional[List[str]] = None) -> str:
        """
        Scans for missing localized names/descriptions in target languages.
        """
        langs = languages or ["zh_TW", "en", "zh_CN"]
        langs_str = '["' + '", "'.join(langs) + '"]'
        cat_filter = f'WHERE {{catalogVersion}} IN (SELECT {{pk}} FROM {{CatalogVersion}} WHERE {{catalog}} IN (SELECT {{pk}} FROM {{Catalog}} WHERE {{id}}=\'{catalog_id}\'))' if catalog_id else ''

        groovy_script = f"""
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery
import de.hybris.platform.servicelayer.i18n.CommonI18NService
import java.util.Locale

def i18nService = spring.getBean("commonI18NService", CommonI18NService)
def query = new FlexibleSearchQuery("SELECT {{pk}} FROM {{{item_type}}} {cat_filter}")
query.setCount(200)
def items = flexibleSearchService.search(query).result

def targetLangs = {langs_str}
def stats = [:]
targetLangs.each {{ stats[it] = 0 }}
def missingSamples = [:]
targetLangs.each {{ missingSamples[it] = [] }}

items.each {{ item ->
    targetLangs.each {{ langCode ->
        try {{
            def loc = i18nService.getLocaleForLanguage(i18nService.getLanguage(langCode))
            def val = item.getName(loc)
            if (!val || val.trim().isEmpty()) {{
                stats[langCode]++
                if (missingSamples[langCode].size() < 5) {{
                    missingSamples[langCode].add(item.hasProperty('code') ? item.code : item.pk.toString())
                }}
            }}
        }} catch (Exception e) {{
            stats[langCode]++
        }}
    }}
}}

println "=== i18n Completeness Check: {item_type} (Scanned: ${{items.size()}} items) ==="
targetLangs.each {{ langCode ->
    def missing = stats[langCode]
    def rate = items.size() > 0 ? (100.0 - (missing * 100.0 / items.size())).round(1) : 100.0
    if (missing == 0) {{
        println "✅ [${{langCode}}]: 100% complete (0 missing)"
    }} else {{
        println "⚠️ [${{langCode}}]: ${{rate}}% complete (${{missing}} items missing translation)"
        println "   Sample missing items: ${{missingSamples[langCode].join(', ')}}"
    }}
}}
"""
        res = self.client.execute_groovy(script=groovy_script, commit=False)
        return res.get("outputText", "").strip() or res.get("stacktraceText", "")
