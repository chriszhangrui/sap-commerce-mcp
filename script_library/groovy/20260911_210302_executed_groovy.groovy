// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:03:02
// Tags: 

def query = flexibleSearchService.search("""
    SELECT count({pr.pk}) FROM {ProductReference AS pr JOIN Product AS p ON {pr.source}={p.pk}}
    WHERE {p.code} LIKE 'COKE%' OR {p.code} LIKE 'SPRITE%' OR {p.code} LIKE 'BONAQUA%'
""").result

return "Existing ProductReferences for Swire products: " + query[0]
