// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:06:39
// Tags: 

def site = baseSiteService.getBaseSiteForUID("powertools-spa")
def stores = site?.stores
def catalogs = stores?.collect { it.catalogs?.collect { c -> c.id } }

return [
    siteUid: site?.uid,
    stores: stores?.collect { it.uid },
    catalogs: catalogs
]
