// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:17:20
// Tags: 

import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.catalog.CatalogVersionService
import de.hybris.platform.core.model.product.ProductModel
import java.util.Locale

def flex = spring.getBean("flexibleSearchService")
def query = """
SELECT {p.pk} FROM {Product AS p JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}} 
WHERE {c.id}='powertoolsProductCatalog' AND {cv.version}='Online' 
AND ({p.code} LIKE 'swire%' OR {p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' 
  OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'SCHWEPPES%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'NESCAFE%' 
  OR {p.code} LIKE 'NESTEA%' OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'CHUN%' OR {p.code} LIKE 'MM-%' 
  OR {p.code} LIKE 'HIC-%' OR {p.code} LIKE 'OASIS%' OR {p.code} LIKE 'HEALTH%')
"""

def products = flex.search(query).result
def summary = [:]
products.each { p ->
  def prefix = p.code.split(/[-_]/)[0]
  summary[prefix] = (summary[prefix] ?: 0) + 1
}

println "Total Swire products: ${products.size()}"
println "Breakdown by prefix:"
summary.sort { -it.value }.each { k, v ->
  println "  ${k.padRight(15)}: ${v}"
}
