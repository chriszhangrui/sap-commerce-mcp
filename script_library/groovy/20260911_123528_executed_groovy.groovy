// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 12:35:28
// Tags: 

import de.hybris.platform.cms2.model.site.CMSSiteModel
def site = flexibleSearchService.search("SELECT {pk} FROM {CMSSite} WHERE {uid}='powertools-spa'").result[0]
println "urlPatterns: " + site.urlPatterns
