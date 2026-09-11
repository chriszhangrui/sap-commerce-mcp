// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 18:23:03
// Tags: 

import de.hybris.platform.enumeration.EnumerationService

def enumVal = enumerationService.getEnumerationValues("SiteTheme")
println "Current SiteThemes: " + enumVal.collect { it.code }
