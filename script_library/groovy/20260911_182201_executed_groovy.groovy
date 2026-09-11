// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 18:22:01
// Tags: 

import de.hybris.platform.core.model.type.ComposedTypeModel
import de.hybris.platform.core.model.enumeration.EnumerationMetaTypeModel

def st = typeService.getComposedTypeForCode("SiteTheme")
println "SiteTheme type: ${st.class.simpleName}, isEnum=${st instanceof EnumerationMetaTypeModel}"
