// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 14:52:45
// Tags: 

import de.hybris.platform.cms2.model.site.CMSSiteModel
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def fss = spring.getBean("flexibleSearchService")
def sites = fss.search(new FlexibleSearchQuery("SELECT {pk} FROM {CMSSite}")).result

def table = []
sites.each { s ->
    def stores = s.stores ? s.stores.collect { it.uid }.join(", ") : "-"
    def ccs = s.contentCatalogs ? s.contentCatalogs.collect { it.id }.join(", ") : "-"
    def langs = s.defaultLanguage ? s.defaultLanguage.isocode : "-"
    def curr = (s.stores && s.stores[0].defaultCurrency) ? s.stores[0].defaultCurrency.isocode : "-"
    table.add("| `${s.uid}` | ${s.name ?: s.uid} | ${s.channel?.code ?: '-'} | `${stores}` | `${ccs}` | ${langs} / ${curr} | ${s.active ? '🟢 激活' : '⚪ 禁用'} |")
}

println """| 站点 UID | 站点名称 | 渠道 | 关联店铺 (BaseStore) | 绑定内容目录 (ContentCatalogs) | 语言/币种 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
""" + table.join("\n")
