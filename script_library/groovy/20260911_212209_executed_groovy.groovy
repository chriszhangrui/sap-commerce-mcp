// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:22:09
// Tags: 

import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.servicelayer.model.ModelService
import de.hybris.platform.catalog.enums.ProductReferenceTypeEnum

def flex = spring.getBean("flexibleSearchService")
def modelService = spring.getBean("modelService")

def compQuery = """
SELECT {c.pk} FROM {ProductReferencesComponent AS c JOIN CatalogVersion AS cv ON {c.catalogVersion}={cv.pk} JOIN Catalog AS cat ON {cv.catalog}={cat.pk}} 
WHERE {cat.id}='powertools-spaContentCatalog' AND {c.uid} IN ('Similar', 'CartSuggestions')
"""
def comps = flex.search(compQuery).result
comps.each { comp ->
  comp.setProductReferenceTypes([ProductReferenceTypeEnum.SIMILAR])
  modelService.save(comp)
  println "Set ${comp.uid} in ${comp.catalogVersion.version} to [SIMILAR]"
}
