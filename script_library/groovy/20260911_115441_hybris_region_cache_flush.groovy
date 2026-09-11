// Verified Script: hybris_region_cache_flush
// Category: cache_ops | Client: Generic
// Date: 2026-09-11 11:54:41
// Tags: cache, region_cache, flush

import de.hybris.platform.core.Registry
def cache = Registry.getCurrentTenant().getCache()
cache.clear()
println "Hybris Region Cache flushed successfully."
