// Verified Script: solr_inprocess_full_reindex
// Category: search_solr | Client: Generic
// Date: 2026-09-11 11:54:41
// Tags: solr, reindex, cronjob_bypass

import de.hybris.platform.solrfacetsearch.config.FacetSearchConfig
import de.hybris.platform.solrfacetsearch.model.config.SolrFacetSearchConfigModel
import de.hybris.platform.solrfacetsearch.config.FacetSearchConfigService
import de.hybris.platform.solrfacetsearch.indexer.IndexerService
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def indexerService = spring.getBean("indexerService", IndexerService.class)
def facetConfigService = spring.getBean("facetSearchConfigService", FacetSearchConfigService.class)

def fsq = new FlexibleSearchQuery("SELECT {pk} FROM {SolrFacetSearchConfig}")
def configs = flexibleSearchService.search(fsq).result

configs.each { SolrFacetSearchConfigModel cfgModel ->
    def name = cfgModel.getName()
    FacetSearchConfig cfg = facetConfigService.getConfiguration(name)
    indexerService.performFullIndex(cfg)
    println "Indexed: " + name
}
