// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 14:57:11
// Tags: 

import de.hybris.platform.cms2lib.model.components.ProductCarouselComponentModel
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def fss = spring.getBean("flexibleSearchService")
def c1 = fss.search(new FlexibleSearchQuery("SELECT {c.pk} FROM {ProductCarouselComponent AS c JOIN CatalogVersion AS cv ON {c.catalogVersion}={cv.pk}} WHERE {cv.version}='Online' AND {c.uid} LIKE '%Powertools%'")).result

c1.collect { [it.uid, it.products?.size()] }.toString()