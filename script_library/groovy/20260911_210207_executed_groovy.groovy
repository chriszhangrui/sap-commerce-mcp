// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:02:07
// Tags: 

def query = flexibleSearchService.search("SELECT {pk} FROM {ProductReferencesComponent}").result

def res = query.findAll { it.catalogVersion?.catalog?.id?.contains("powertools") }.collect { comp ->
    [
        uid: comp.uid,
        catalog: comp.catalogVersion?.catalog?.id,
        version: comp.catalogVersion?.version,
        title: comp.title,
        referenceTypes: comp.productReferenceTypes?.collect { it.code }
    ]
}

return groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(res))
