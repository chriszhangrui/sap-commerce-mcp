// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:19:43
// Tags: 

import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.servicelayer.model.ModelService
import de.hybris.platform.core.model.product.ProductModel
import de.hybris.platform.catalog.model.ProductReferenceModel
import de.hybris.platform.catalog.enums.ProductReferenceTypeEnum
import java.util.Locale

def flex = spring.getBean("flexibleSearchService")
def modelService = spring.getBean("modelService")

// 1. Delete existing ProductReference for Swire products in powertoolsProductCatalog
def delQuery = """
SELECT {pr.pk} FROM {ProductReference AS pr JOIN Product AS p ON {pr.source}={p.pk} JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}}
WHERE {c.id}='powertoolsProductCatalog'
AND ({p.code} LIKE 'swire%' OR {p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' 
  OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'SCHWEPPES%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'NESCAFE%' 
  OR {p.code} LIKE 'NESTEA%' OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'CHUN%' OR {p.code} LIKE 'MM-%' 
  OR {p.code} LIKE 'HIC-%' OR {p.code} LIKE 'OASIS%' OR {p.code} LIKE 'HEALTH%')
"""
def oldRefs = flex.search(delQuery).result
println "Removing ${oldRefs.size()} old references..."
modelService.removeAll(oldRefs)

// 2. Query products for each catalog version
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

int totalCreated = 0

['Online', 'Staged'].each { version ->
  def params = [version: version]
  List<ProductModel> products = flex.search(swireQuery, params).result
  println "Processing ${products.size()} products in ${version}..."
  
  def byPrefix = [:].withDefault { [] }
  def byMacro = [:].withDefault { [] }
  
  products.each { p ->
    def prefix = p.code.split(/[-_]/)[0]
    byPrefix[prefix] << p
    def macro = macroCategories[prefix] ?: 'OTHER'
    byMacro[macro] << p
  }
  
  def refsToSave = []
  
  products.each { p ->
    def prefix = p.code.split(/[-_]/)[0]
    def macro = macroCategories[prefix] ?: 'OTHER'
    
    // SIMILAR: 4 candidates
    def sameBrand = byPrefix[prefix].findAll { it.code != p.code }
    def sameMacro = byMacro[macro].findAll { it.code != p.code && !sameBrand.contains(it) }
    
    def similarTargets = []
    similarTargets.addAll(sameBrand.take(4))
    if (similarTargets.size() < 4) {
      similarTargets.addAll(sameMacro.take(4 - similarTargets.size()))
    }
    
    similarTargets.each { target ->
      def ref = modelService.create(ProductReferenceModel.class)
      ref.setSource(p)
      ref.setTarget(target)
      ref.setReferenceType(ProductReferenceTypeEnum.SIMILAR)
      ref.setActive(Boolean.TRUE)
      ref.setPreselected(Boolean.FALSE)
      refsToSave << ref
    }
    
    // CROSSELLING: 3 candidates from other macro-categories
    def otherMacros = ['SODA', 'WATER', 'TEA_JUICE', 'COFFEE_ENERGY'] - [macro]
    otherMacros.each { otherM ->
      def candidates = byMacro[otherM]
      if (candidates) {
        int idx = Math.abs(p.code.hashCode()) % candidates.size()
        def target = candidates[idx]
        def ref = modelService.create(ProductReferenceModel.class)
        ref.setSource(p)
        ref.setTarget(target)
        ref.setReferenceType(ProductReferenceTypeEnum.CROSSELLING)
        ref.setActive(Boolean.TRUE)
        ref.setPreselected(Boolean.FALSE)
        refsToSave << ref
      }
    }
  }
  
  modelService.saveAll(refsToSave)
  println "Saved ${refsToSave.size()} references for ${version}"
  totalCreated += refsToSave.size()
}

// 3. Update ProductReferencesComponents in powertools-spaContentCatalog
def compQuery = """
SELECT {c.pk} FROM {ProductReferencesComponent AS c JOIN CatalogVersion AS cv ON {c.catalogVersion}={cv.pk} JOIN Catalog AS cat ON {cv.catalog}={cat.pk}} 
WHERE {cat.id}='powertools-spaContentCatalog' AND {c.uid} IN ('Similar', 'CartSuggestions')
"""
def comps = flex.search(compQuery).result
comps.each { comp ->
  comp.setProductReferenceTypes([ProductReferenceTypeEnum.SIMILAR, ProductReferenceTypeEnum.CROSSELLING])
  comp.setTitle("為您推薦 / 相似熱銷飲品", Locale.TRADITIONAL_CHINESE)
  comp.setTitle("为您推荐 / 相似热销饮品", Locale.SIMPLIFIED_CHINESE)
  comp.setTitle("You may also like...", Locale.ENGLISH)
  modelService.save(comp)
  println "Updated component ${comp.uid} in ${comp.catalogVersion.version}"
}

println "SUCCESS! Created ${totalCreated} total ProductReferences and updated ${comps.size()} CMS components."
