// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 14:52:29
// Tags: 

import de.hybris.platform.cms2.model.site.CMSSiteModel
import de.hybris.platform.catalog.CatalogVersionService

def cvs = spring.getBean("catalogVersionService")
def fss = spring.getBean("flexibleSearchService")

def q = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery("SELECT {pk} FROM {CMSSite} WHERE {uid}='powertools-spa'")
def sites = fss.search(q).result
if (sites) {
    def s = sites[0]
    println "Site: " + s.uid
    println "ContentCatalogs: " + s.contentCatalogs.collect { it.id }
}
