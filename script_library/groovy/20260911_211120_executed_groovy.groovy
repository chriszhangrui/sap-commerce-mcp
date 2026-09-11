// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:11:20
// Tags: 

def query = flexibleSearchService.search("""
    SELECT {p.pk} FROM {Product AS p JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}}
    WHERE {c.id} = 'powertoolsProductCatalog' AND {cv.version} = 'Online'
    AND ({p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' 
      OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'NESCAFE%' OR {p.code} LIKE 'NESTEA%' 
      OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'CHUN%' 
      OR {p.code} LIKE 'HIC%' OR {p.code} LIKE 'MM-%' OR {p.code} LIKE 'SCHWEPPES%' 
      OR {p.code} LIKE 'HEALTH%' OR {p.code} LIKE 'SOYA%' OR {p.code} LIKE 'OATS%'
      OR {p.code} LIKE 'PREDATOR%' OR {p.code} LIKE 'COSTA%')
""").result

return query.collect { it.code }.sort()
