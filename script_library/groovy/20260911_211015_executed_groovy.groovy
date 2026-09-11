// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:10:15
// Tags: 

import de.hybris.platform.catalog.model.CatalogVersionModel

def catalog = catalogVersionService.getCatalogVersion("powertoolsProductCatalog", "Online")

def query = flexibleSearchService.search("""
    SELECT {p.pk} FROM {Product AS p}
    WHERE {p.catalogVersion} = ?cv
    AND ({p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' 
      OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'NESCAFE%' OR {p.code} LIKE 'NESTEA%' 
      OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'CHUN%' 
      OR {p.code} LIKE 'HIC%' OR {p.code} LIKE 'MM-%' OR {p.code} LIKE 'SCHWEPPES%' 
      OR {p.code} LIKE 'HEALTH%' OR {p.code} LIKE 'SOYA%' OR {p.code} LIKE 'OATS%'
      OR {p.code} LIKE 'PREDATOR%' OR {p.code} LIKE 'COSTA%')
""", [cv: catalog]).result

def allProds = query
def codeToProd = allProds.collectEntries { [(it.code): it] }

// Helper to determine brand prefix
def getPrefix = { String code ->
    def parts = code.split("-")
    if (code.startsWith("MM-")) return "MM"
    if (code.startsWith("CHUN-")) return "CHUN"
    if (code.startsWith("HIC-")) return "HIC"
    return parts[0]
}

def createdCount = 0
def samplePairs = []

allProds.each { prod ->
    def prefix = getPrefix(prod.code)
    def sameBrand = allProds.findAll { it.code != prod.code && getPrefix(it.code) == prefix }
    def diffBrand = allProds.findAll { getPrefix(it.code) != prefix }

    // Pick up to 4 similar (same brand first, then diff brand)
    def similar = (sameBrand.take(4) + diffBrand.take(Math.max(0, 4 - sameBrand.size()))).take(4)

    // Pick 2 cross-sell (essential B2B staples: Coke, Bonaqua, Chun Oolong, Nescafe, Monster)
    def stapleCodes = ["COKE-330-CAN-24P", "BONAQUA-500-PET-24P", "CHUN-OOLONG-500-PET-24P", "NESCAFE-REG-250-CAN-24P", "MONSTER-CLASSIC-355-CAN-24P", "SPRITE-330-CAN-24P"]
    def cross = stapleCodes.findAll { it != prod.code && !similar.any { s -> s.code == it } }.take(3).collect { codeToProd[it] }.findAll { it != null }

    createdCount += similar.size() + cross.size()
    if (samplePairs.size() < 3) {
        samplePairs << [
            source: prod.code,
            similar: similar.collect { it.code },
            cross: cross.collect { it.code }
        ]
    }
}

return [
    totalProducts: allProds.size(),
    totalReferencesToCreatePerVersion: createdCount,
    samples: samplePairs
]
