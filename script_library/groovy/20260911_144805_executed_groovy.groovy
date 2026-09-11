// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 14:48:05
// Tags: 

import de.hybris.platform.cms2.model.site.CMSSiteModel
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def fss = spring.getBean("flexibleSearchService")
def sites = fss.search(new FlexibleSearchQuery("SELECT {pk} FROM {CMSSite}")).result

def out = []
sites.each { s ->
    def cc = s.contentCatalogs ? s.contentCatalogs.collect { it.id } : []
    def dc = s.defaultContentCatalog ? s.defaultContentCatalog.id : null
    out.add("Site: ${s.uid}, Name: ${s.name}, DefaultCC: ${dc}, ContentCatalogs: ${cc}")
}
out.join("\n")