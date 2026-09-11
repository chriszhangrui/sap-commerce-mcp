// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:19:24
// Tags: 

import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.servicelayer.model.ModelService
import de.hybris.platform.core.model.product.ProductModel
import de.hybris.platform.catalog.model.ProductReferenceModel
import de.hybris.platform.catalog.enums.ProductReferenceTypeEnum

def flex = spring.getBean("flexibleSearchService")

def swireQuery = """
SELECT {p.pk} FROM {Product AS p JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}} 
WHERE {c.id}='powertoolsProductCatalog' AND {cv.version}=?version 
AND ({p.code} LIKE 'swire%' OR {p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' 
  OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'SCHWEPPES%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'NESCAFE%' 
  OR {p.code} LIKE 'NESTEA%' OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'CHUN%' OR {p.code} LIKE 'MM-%' 
  OR {p.code} LIKE 'HIC-%' OR {p.code} LIKE 'OASIS%' OR {p.code} LIKE 'HEALTH%')
"""

def macroCategories = [
  'COKE': 'SODA', 'SPRITE': 'SODA', 'FANTA': 'SODA', 'SCHWEPPES': 'SODA',
  'BONAQUA': 'WATER', 'AQUARIUS': 'WATER',
  'HIC': 'TEA_JUICE', 'NESTEA': 'TEA_JUICE', 'MM': 'TEA_JUICE',
  'NESCAFE': 'COFFEE_ENERGY', 'MONSTER': 'COFFEE_ENERGY', 'CHUN': 'COFFEE_ENERGY'
]

def sampleOutput = []
['Online', 'Staged'].each { version ->
  def params = [version: version]
  List<ProductModel> products = flex.search(swireQuery, params).result
  println "Found ${products.size()} products in ${version}"
  
  // Group products by brand prefix and macro-category
  def byPrefix = [:].withDefault { [] }
  def byMacro = [:].withDefault { [] }
  
  products.each { p ->
    def prefix = p.code.split(/[-_]/)[0]
    byPrefix[prefix] << p
    def macro = macroCategories[prefix] ?: 'OTHER'
    byMacro[macro] << p
  }
  
  int totalSimilar = 0
  int totalCross = 0
  
  products.each { p ->
    def prefix = p.code.split(/[-_]/)[0]
    def macro = macroCategories[prefix] ?: 'OTHER'
    
    // 1. SIMILAR: 4 candidates
    // Prefer same prefix (excluding self)
    def sameBrand = byPrefix[prefix].findAll { it.code != p.code }
    // If not enough, supplement with same macro-category
    def sameMacro = byMacro[macro].findAll { it.code != p.code && !sameBrand.contains(it) }
    
    def similarTargets = []
    similarTargets.addAll(sameBrand.take(4))
    if (similarTargets.size() < 4) {
      similarTargets.addAll(sameMacro.take(4 - similarTargets.size()))
    }
    
    // 2. CROSSELLING: 3 candidates from other macro-categories
    def otherMacros = ['SODA', 'WATER', 'TEA_JUICE', 'COFFEE_ENERGY'] - [macro]
    def crossTargets = []
    otherMacros.each { otherM ->
      def candidates = byMacro[otherM]
      if (candidates) {
        int idx = Math.abs(p.code.hashCode()) % candidates.size()
        crossTargets << candidates[idx]
      }
    }
    
    totalSimilar += similarTargets.size()
    totalCross += crossTargets.size()
    
    if (sampleOutput.size() < 4 && version == 'Online') {
      sampleOutput << [
        product: p.code,
        name: p.name,
        similar: similarTargets.collect { it.code },
        cross: crossTargets.collect { it.code }
      ]
    }
  }
  
  println "${version}: Generated ${totalSimilar} SIMILAR + ${totalCross} CROSSELLING references across ${products.size()} products"
}

sampleOutput.each { s ->
  println "SAMPLE: ${s.product} (${s.name}):"
  println "  Similar: ${s.similar.join(', ')}"
  println "  Cross:   ${s.cross.join(', ')}"
}
