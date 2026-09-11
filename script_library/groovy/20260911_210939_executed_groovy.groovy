// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:09:39
// Tags: 

def query = flexibleSearchService.search("""
    SELECT {p.pk} FROM {Product AS p JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}}
    WHERE {c.id} = 'powertoolsProductCatalog' AND {cv.version} = 'Online'
    AND {p.code} NOT LIKE '3%' AND {p.code} NOT LIKE '1%' AND {p.code} NOT LIKE '2%' AND {p.code} NOT LIKE '4%' 
    AND {p.code} NOT LIKE '5%' AND {p.code} NOT LIKE '6%' AND {p.code} NOT LIKE '7%' AND {p.code} NOT LIKE '8%' AND {p.code} NOT LIKE '9%'
""").result

def prods = query.collect { p ->
    [
        code: p.code,
        name: p.name,
        categories: p.supercategories?.collect { it.code }?.findAll { it.startsWith("swire_") || it.startsWith("brand_") }
    ]
}

return "Total non-powertools (Swire) products in Online: " + prods.size()
