// Verified Script: promo_promo_b2b_tier_spring_2026
// Category: promotions_drools | Client: Generic
// Date: 2026-09-11 14:31:52
// Tags: promotions, drools, order_threshold_discount, usd

import de.hybris.platform.core.Registry
import de.hybris.platform.promotionengineservices.model.PromotionSourceRuleModel
import de.hybris.platform.ruleengineservices.model.RuleEngineCronJobModel
import de.hybris.platform.promotions.model.PromotionGroupModel
import de.hybris.platform.ruleengineservices.enums.RuleStatus
import groovy.json.JsonOutput

def modelService = spring.getBean("modelService")
def flexibleSearchService = spring.getBean("flexibleSearchService")
def cronJobService = spring.getBean("cronJobService")

println "=== 开始部署促销规则: promo_b2b_tier_spring_2026 ==="

// 1. 获取目标 PromotionGroup
def pgList = flexibleSearchService.search("SELECT {pk} FROM {PromotionGroup} WHERE {Identifier} = 'powertoolsPromoGrp'").result
def promoGroup = pgList ? pgList[0] : flexibleSearchService.search("SELECT {pk} FROM {PromotionGroup}").result[0]

// 2. 清理历史同名规则
def oldRules = flexibleSearchService.search("SELECT {pk} FROM {PromotionSourceRule} WHERE {code} = 'promo_b2b_tier_spring_2026'").result
if (oldRules) {
    println "清理同名旧规则: " + oldRules.size() + " 条"
    modelService.removeAll(oldRules)
}

// 3. 构建新 PromotionSourceRuleModel
def rule = modelService.create(PromotionSourceRuleModel)
rule.code = "promo_b2b_tier_spring_2026"
rule.name = '【企业春季订货特惠】订单满 ,000 立减 '
rule.description = 'B2B 采购特惠：订单小计金额达到 ,000 时立减  并输出通知'
rule.priority = 250
rule.maxAllowedRuns = 1
rule.stackable = true
rule.status = RuleStatus.UNPUBLISHED
rule.website = promoGroup


def cond = [
    [
        definitionId: "y_cart_total",
        parameters: [
            value: [
                type: "Map(ItemType(Currency),java.math.BigDecimal)",
                value: [ (USD): 1000.0 ]
            ],
            operator: [
                type: "Enum(de.hybris.platform.ruledefinitions.AmountOperator)",
                value: "GREATER_THAN_OR_EQUAL"
            ]
        ],
        children: []
    ]
]

def act = [
    [
        definitionId: "y_order_fixed_discount",
        parameters: [
            value: [
                type: "Map(ItemType(Currency),java.math.BigDecimal)",
                value: [ (USD): 100.0 ]
            ]
        ]
    ]
]


rule.conditions = JsonOutput.toJson(cond)
rule.actions = JsonOutput.toJson(act)
rule.messageFired = '恭喜！订单已满 USD 1000.0，已为您立减 USD 100.0！'
modelService.save(rule)
println "创建 PromotionSourceRuleModel 成功: " + rule.code


// ----------------------------------------------------------------------------------
// 触发规则编译与发布 CronJob
// ----------------------------------------------------------------------------------
def jobList = flexibleSearchService.search("SELECT {pk} FROM {ServicelayerJob} WHERE {code} = 'rules -> Compilation and Publishing for [promotions-module]'").result
if (!jobList) {
    println "警告: 未找到 'rules -> Compilation and Publishing for [promotions-module]' Job，尝试使用常规 CronJob 触发"
} else {
    def job = jobList[0]
    def cronJob = modelService.create(RuleEngineCronJobModel)
    cronJob.code = "mcpPromotionPublishCronJob_" + System.currentTimeMillis()
    cronJob.job = job
    cronJob.sourceRules = [rule]
    cronJob.targetModuleName = "promotions-module"
    cronJob.enableIncrementalUpdate = true
    def adminList = flexibleSearchService.search("SELECT {pk} FROM {Employee} WHERE {uid}='admin'").result
    if (adminList) {
        cronJob.sessionUser = adminList[0]
    }
    modelService.save(cronJob)

    def mod = flexibleSearchService.search("SELECT {pk} FROM {AbstractRulesModule} WHERE {name} = 'promotions-module'").result[0]
    mod.lockAcquired = false
    modelService.save(mod)

    println "正在提交事务并触发规则编译 CronJob: " + cronJob.code
    if (de.hybris.platform.tx.Transaction.current().isRunning()) {
        de.hybris.platform.tx.Transaction.current().commit()
    }
    cronJobService.performCronJob(cronJob, false)
    println "=== 促销规则已部署，Drools 规则编译任务已提交后台执行 ==="
}

