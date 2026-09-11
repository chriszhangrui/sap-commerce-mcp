// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:05:41
// Tags: 

def query = flexibleSearchService.search("""
    SELECT DISTINCT {p.pk} FROM {ProductReference AS pr JOIN Product AS p ON {pr.source}={p.pk} JOIN CatalogVersion AS cv ON {p.catalogVersion}={cv.pk} JOIN Catalog AS c ON {cv.catalog}={c.pk}}
    WHERE {c.id} = 'powertoolsProductCatalog' AND {cv.version} = 'Online'
""").result

return "Powertools Online products with references count: " + query.size() + ", samples: " + query.take(5).collect { it.code }
