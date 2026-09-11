// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:03:29
// Tags: 

def pr = flexibleSearchService.search("SELECT {pk} FROM {ProductReference}").result.find { it != null }

return [
    sourceCode: pr.source?.code,
    targetCode: pr.target?.code,
    referenceType: pr.referenceType?.code,
    active: pr.active,
    preselected: pr.preselected,
    quantity: pr.quantity,
    description: pr.description
]
