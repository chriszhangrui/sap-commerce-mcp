// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:53:12
// Tags: 

import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.servicelayer.model.ModelService
import de.hybris.platform.core.model.product.ProductModel

def flex = spring.getBean("flexibleSearchService")
def modelService = spring.getBean("modelService")

def swireQuery = """
SELECT {p.pk} FROM {Product AS p JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}} 
WHERE {c.id}='powertoolsProductCatalog' AND {cv.version}=?version 
AND ({p.code} LIKE 'swire%' OR {p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' 
  OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'SCHWEPPES%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'NESCAFE%' 
  OR {p.code} LIKE 'NESTEA%' OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'CHUN%' OR {p.code} LIKE 'MM-%' 
  OR {p.code} LIKE 'HIC-%' OR {p.code} LIKE 'OASIS%' OR {p.code} LIKE 'HEALTH%')
"""

// Specific preferred sibling mappings for best visual match
def specificSiblingMap = [
  'COKE-192-GLASS-24P': 'COKE-200-GLASS-24P',
  'COKE-330-CAN-12P': 'COKE-330-CAN-8P',
  'COKE-LEMON-330-CAN-8P': 'COKE-330-CAN-8P',
  'COKE-NS-2000-PET-6P': 'COKE-2000-PET-6P',
  'COKE-NS-330-CAN-12P': 'COKE-NS-330-CAN-8P',
  'COKE-NS-330-CAN-4P': 'COKE-NS-330-CAN-8P',
  'BONAQUA-2000-PET-6P': 'BONAQUA-1500-PET-12P',
  'BONAQUA-LEM-500-PET-24P': 'BONAQUA-500-PET-24P',
  'BONAQUA-LIME-500-PET-24P': 'BONAQUA-500-PET-24P',
  'CHUN-BARLEY-500-PET-24P': 'CHUN-GREEN-500-PET-24P',
  'CHUN-OULONG-1250-PET-12P': 'CHUN-OOLONG-920-PET-12P',
  'CHUN-OULONG-500-PET-24P': 'CHUN-OOLONG-500-PET-24P',
  'CHUN-PUER-500-PET-24P': 'CHUN-DAHONGPAO-500-PET-24P',
  'HIC-LEMON-500-PET-24P': 'HIC-LEMON-250-PP-24P',
  'HIC-PEACH-250-PP-24P': 'HIC-LEMON-250-PP-24P',
  'MM-ALOE-500-PET-24P': 'MM-ORANGE-200-PP-6P',
  'MM-APPLE-200-PP-6P-X4': 'MM-APPLE-200-PP-24P',
  'MM-ORANGE-1250-PET-12P': 'MM-ORANGE-200-PP-6P',
  'MM-ORANGE-500-PET-24P': 'MM-ORANGE-200-PP-6P',
  'MM-WHITEGRAPE-500-PET-24P': 'MM-ORANGE-200-PP-6P',
  'MONSTER-REG-355-CAN-24P': 'MONSTER-CLASSIC-355-CAN-24P',
  'MONSTER-ZERO-355-CAN-24P': 'MONSTER-ULTRA-355-CAN-24P',
  'NESCAFE-AMERICANO-250-CAN-24P': 'NESCAFE-AME-270-PET-15P',
  'NESCAFE-LATTE-250-CAN-24P': 'NESCAFE-REG-250-CAN-24P',
  'NESCAFE-WHITE-250-CAN-24P': 'NESCAFE-REG-250-CAN-24P',
  'NESTEA-ICE-480-PET-24P': 'NESTEA-ICE-LEMON-480-PET-24P',
  'SCHWEPPES-CREAM-330-CAN-8P': 'SCHWEPPES-CREAM-330-CAN-24P',
  'AQUARIUS-SPARK-500-PET-24P': 'AQUARIUS-500-PET-24P'
]

int totalEnriched = 0

['Online', 'Staged'].each { version ->
  List<ProductModel> products = flex.search(swireQuery, [version: version]).result
  def mapByCode = products.collectEntries { [(it.code): it] }
  
  def withoutPic = products.findAll { it.picture == null }
  println "${version}: Found ${withoutPic.size()} products without picture."
  
  withoutPic.each { p ->
    def donorCode = specificSiblingMap[p.code]
    def donor = donorCode ? mapByCode[donorCode] : null
    if (!donor || donor.picture == null) {
      // fallback to any with same prefix
      def prefix = p.code.split(/[-_]/)[0]
      donor = products.find { it.code != p.code && it.code.startsWith(prefix) && it.picture != null }
    }
    
    if (donor && donor.picture != null) {
      p.setPicture(donor.picture)
      p.setThumbnail(donor.thumbnail)
      p.setDetail(donor.detail)
      p.setNormal(donor.normal)
      p.setThumbnails(donor.thumbnails)
      p.setGalleryImages(donor.galleryImages)
      modelService.save(p)
      totalEnriched++
      println "  [${version}] ${p.code} <- inherited from ${donor.code}"
    } else {
      println "  [${version}] WARNING: No donor found for ${p.code}"
    }
  }
}

println "SUCCESS: Enriched ${totalEnriched} product entries with high-res sibling images!"
