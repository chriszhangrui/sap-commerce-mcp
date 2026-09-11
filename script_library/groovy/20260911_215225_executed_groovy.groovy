// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:52:25
// Tags: 

import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.core.model.product.ProductModel
import de.hybris.platform.core.model.media.MediaModel

def flex = spring.getBean("flexibleSearchService")

def query = """
SELECT {p.pk} FROM {Product AS p JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}} 
WHERE {c.id}='powertoolsProductCatalog' AND {cv.version}='Online' 
AND ({p.code} LIKE 'swire%' OR {p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' 
  OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'SCHWEPPES%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'NESCAFE%' 
  OR {p.code} LIKE 'NESTEA%' OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'CHUN%' OR {p.code} LIKE 'MM-%' 
  OR {p.code} LIKE 'HIC-%' OR {p.code} LIKE 'OASIS%' OR {p.code} LIKE 'HEALTH%')
"""

List<ProductModel> allProducts = flex.search(query).result
def withPic = allProducts.findAll { it.picture != null }
def withoutPic = allProducts.findAll { it.picture == null }

println "With pic: ${withPic.size()}, Without pic: ${withoutPic.size()}"

withoutPic.each { p ->
  def prefix = p.code.split(/[-_]/)[0]
  def donor = withPic.find { it.code.startsWith(prefix) }
  println "Match ${p.code} -> ${donor?.code} (pic: ${donor?.picture?.code})"
}
