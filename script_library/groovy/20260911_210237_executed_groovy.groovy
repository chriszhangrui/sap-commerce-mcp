// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:02:37
// Tags: 

def query = flexibleSearchService.search("""
    SELECT {p.pk} FROM {Product AS p JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}}
    WHERE {c.id} = 'powertoolsProductCatalog' AND {cv.version} = 'Online'
    AND ({p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'FANTA%' OR {p.code} LIKE 'BONAQUA%' OR {p.code} LIKE 'NESCAFE%' OR {p.code} LIKE 'NESTEA%' OR {p.code} LIKE 'MONSTER%' OR {p.code} LIKE 'AQUARIUS%' OR {p.code} LIKE 'CHUN%' OR {p.code} LIKE 'HIC%' OR {p.code} LIKE 'MM-%' OR {p.code} LIKE 'SCHWEPPES%' OR {p.code} LIKE 'HEALTH%')
""").result

def prods = query.collect { p ->
    [
        code: p.code,
        name: p.name,
        categories: p.supercategories?.collect { it.code }
    ]
}

return "Total Swire Online Products found: " + prods.size() + "\n" + groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(prods.take(10)))
