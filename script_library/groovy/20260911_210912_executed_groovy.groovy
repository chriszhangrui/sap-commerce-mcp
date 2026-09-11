// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:09:12
// Tags: 

def query = flexibleSearchService.search("""
    SELECT {csft.pk} FROM {ContentSlotForTemplate AS csft JOIN PageTemplate AS p ON {csft.pageTemplate}={p.pk}}
    WHERE {p.uid} LIKE '%ProductDetails%'
""").result

def list = query.collect { csft ->
    [
        position: csft.position,
        template: csft.pageTemplate?.uid,
        slotUid: csft.contentSlot?.uid,
        components: csft.contentSlot?.cmsComponents?.collect { c -> [uid: c.uid, type: c.itemtype] }
    ]
}

return groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(list))
