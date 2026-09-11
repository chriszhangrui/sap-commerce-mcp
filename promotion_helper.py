#!/usr/bin/env python3
import os
import json
import re
import datetime
from typing import Optional, Dict, Any, List
from hac_client import HACClient
from script_manager import ScriptManager

class PromotionHelper:
    """
    Helper for scaffolding, configuring, compiling, and publishing Promotion Source Rules
    (Drools Promotion Engine) in SAP Commerce Cloud (Hybris).
    """

    def __init__(self, client: HACClient, script_manager: Optional[ScriptManager] = None):
        self.client = client
        self.script_mgr = script_manager or ScriptManager()

    def list_promotions(
        self,
        promo_group: Optional[str] = None,
        status: Optional[str] = None,
        lang: str = "zh"
    ) -> str:
        """
        Queries and lists existing PromotionSourceRules via FlexibleSearch.
        """
        where_clauses = []
        if promo_group:
            where_clauses.append(f"{{pg.Identifier}} = '{promo_group}'")
        if status and status.upper() != "ALL":
            where_clauses.append(f"{{rs.code}} = '{status.upper()}'")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
        SELECT {{psr.code}}, {{psr.name}}, {{rs.code}}, {{psr.priority}}
        FROM {{PromotionSourceRule as psr
              LEFT JOIN RuleStatus as rs ON {{psr.status}}={{rs.pk}}
              LEFT JOIN PromotionGroup as pg ON {{psr.website}}={{pg.pk}}}}
        {where_sql}
        ORDER BY {{psr.priority}} DESC, {{psr.creationtime}} DESC
        """

        try:
            res = self.client.execute_flexsearch(query.strip(), max_count=50)
            rows = res.get("resultList", [])
            count = len(rows)

            is_zh = lang.startswith("zh")
            title = f"🏷️ **=== SAP Commerce 促销规则列表 (共查询到 {count} 条) ===**" if is_zh else f"🏷️ **=== SAP Commerce Promotion Rules List (Found {count}) ===**"

            if not rows:
                msg = "\n当前暂无匹配的促销规则。" if is_zh else "\nNo matching promotion rules found."
                return title + msg

            headers = ["规则编码 (Code)", "促销名称 (Name)", "状态 (Status)", "优先级 (Priority)"] if is_zh else ["Rule Code", "Name", "Status", "Priority"]
            lines = [
                title,
                "",
                f"| {' | '.join(headers)} |",
                f"| {' | '.join(['---'] * len(headers))} |"
            ]

            status_badges = {
                "PUBLISHED": "🟢 已发布 (PUBLISHED)",
                "MODIFIED": "🟡 待重新发布 (MODIFIED)",
                "UNPUBLISHED": "⚪ 未发布 (UNPUBLISHED)",
                "INACTIVE": "🔴 已失效 (INACTIVE)"
            }

            for r in rows:
                if isinstance(r, (list, tuple)):
                    code = str(r[0]) if len(r) > 0 else "-"
                    name = str(r[1]) if len(r) > 1 else "-"
                    st = str(r[2]) if len(r) > 2 else "-"
                    prio = str(r[3]) if len(r) > 3 else "0"
                else:
                    code = r.get("P_CODE") or r.get("code") or "-"
                    name = r.get("P_NAME") or r.get("name") or "-"
                    st = r.get("CODE") or r.get("status") or "-"
                    prio = r.get("P_PRIORITY") or r.get("priority") or "0"
                st_display = status_badges.get(st, st) if is_zh else st
                lines.append(f"| `{code}` | {name} | {st_display} | {prio} |")

            return "\n".join(lines)
        except Exception as e:
            return f"❌ 查询促销规则异常: {e}"

    def scaffold_promotion(
        self,
        rule_code: str,
        name: str,
        description: Optional[str] = None,
        promo_type: str = "ORDER_THRESHOLD_DISCOUNT",
        threshold_amount: Optional[float] = None,
        currency: str = "USD",
        discount_amount: Optional[float] = None,
        discount_percentage: Optional[float] = None,
        qualifying_products: Optional[List[str]] = None,
        gift_product: Optional[str] = None,
        gift_quantity: int = 1,
        target_rule_code: Optional[str] = None,
        message_fired: Optional[str] = None,
        promo_group: str = "powertoolsPromoGrp",
        priority: int = 150,
        compile_immediately: bool = True,
        lang: str = "zh"
    ) -> str:
        """
        Builds, saves, and compiles a PromotionSourceRule in Drools Rule Engine.
        """
        is_zh = lang.startswith("zh")
        clean_code = re.sub(r'[^a-zA-Z0-9_]', '_', rule_code).strip('_')
        desc = description or f"Promotion Rule: {name}"
        curr = currency.upper()

        groovy_script = self._generate_groovy_script(
            rule_code=clean_code,
            name=name,
            description=desc,
            promo_type=promo_type.upper(),
            threshold_amount=threshold_amount,
            currency=curr,
            discount_amount=discount_amount,
            discount_percentage=discount_percentage,
            qualifying_products=qualifying_products or [],
            gift_product=gift_product,
            gift_quantity=gift_quantity,
            target_rule_code=target_rule_code,
            message_fired=message_fired,
            promo_group=promo_group,
            priority=priority,
            compile_immediately=compile_immediately
        )

        try:
            exec_res = self.client.execute_groovy(groovy_script)
            output_text = exec_res.get("executionResult", "") or exec_res.get("outputText", "")

            # Archive to script library
            archive_id = self.script_mgr.archive_script(
                script_type="groovy",
                name=f"promo_{clean_code}",
                content=groovy_script,
                category="promotions_drools",
                client_name="Generic",
                description=f"Drools 促销规则 [{name}] (类型: {promo_type}, 门槛: {threshold_amount} {curr})",
                tags=["promotions", "drools", promo_type.lower(), curr.lower()]
            )

            res_lines = [
                f"🎉 **{'促销规则部署成功' if is_zh else 'Promotion Rule Deployed Successfully'}**",
                f"- **{'规则编码' if is_zh else 'Rule Code'}:** `{clean_code}`",
                f"- **{'促销名称' if is_zh else 'Name'}:** {name}",
                f"- **{'促销类型' if is_zh else 'Type'}:** `{promo_type}`",
                f"- **{'促销组' if is_zh else 'Promotion Group'}:** `{promo_group}`",
                f"- **{'优先级' if is_zh else 'Priority'}:** `{priority}`",
                f"- **{'Drools 即时编译' if is_zh else 'Drools Hot-Compilation'}:** {'⚡ 已触发后台即时编译并挂载' if compile_immediately else '未触发 (待手动发布)'}",
                f"- **{'脚本自动归档' if is_zh else 'Script Archived'}:** `{archive_id}`",
                "",
                f"**{'执行输出摘要' if is_zh else 'Execution Output Summary'}:**",
                "```text",
                output_text.strip() if output_text.strip() else "Execution completed successfully with no errors.",
                "```"
            ]

            return "\n".join(res_lines)
        except Exception as e:
            return f"❌ {'促销规则部署失败' if is_zh else 'Promotion Rule Deployment Failed'}: {e}"

    def _generate_groovy_script(
        self,
        rule_code: str,
        name: str,
        description: str,
        promo_type: str,
        threshold_amount: Optional[float],
        currency: str,
        discount_amount: Optional[float],
        discount_percentage: Optional[float],
        qualifying_products: List[str],
        gift_product: Optional[str],
        gift_quantity: int,
        target_rule_code: Optional[str],
        message_fired: Optional[str],
        promo_group: str,
        priority: int,
        compile_immediately: bool
    ) -> str:
        """
        Generates the Groovy code to build PromotionSourceRuleModel and perform rule compilation.
        """
        if not message_fired:
            if promo_type == "ORDER_THRESHOLD_DISCOUNT":
                if discount_amount:
                    message_fired = f"恭喜！订单已满 {currency} {threshold_amount}，已为您立减 {currency} {discount_amount}！"
                else:
                    message_fired = f"恭喜！订单已满 {currency} {threshold_amount}，已为您立享 {discount_percentage}% 折扣！"
            elif promo_type == "ORDER_THRESHOLD_FREE_GIFT":
                message_fired = f"恭喜！订单已满 {currency} {threshold_amount}，额外获赠 {gift_quantity} 件赠品 [{gift_product}]！"
            elif promo_type == "BUNDLE_FREE_GIFT":
                message_fired = f"恭喜！已满足组合套装条件，获赠 {gift_quantity} 件专属赠品 [{gift_product}]！"
            elif promo_type == "POTENTIAL_MESSAGE":
                message_fired = f"温馨提示：订单满 {currency} {threshold_amount} 即可享受专属特惠与买赠，快去凑单吧！"
            else:
                message_fired = f"恭喜！您已享受优惠：{name}"

        escaped_name = name.replace("'", "\\'")
        escaped_desc = description.replace("'", "\\'")
        escaped_msg = message_fired.replace("'", "\\'")

        condition_action_builder = ""

        if promo_type == "ORDER_THRESHOLD_DISCOUNT":
            thresh = threshold_amount or 100.0
            condition_action_builder = f"""
def cond = [
    [
        definitionId: "y_cart_total",
        parameters: [
            value: [
                type: "Map(ItemType(Currency),java.math.BigDecimal)",
                value: [ "{currency}": {thresh} ]
            ],
            operator: [
                type: "Enum(de.hybris.platform.ruledefinitions.AmountOperator)",
                value: "GREATER_THAN_OR_EQUAL"
            ]
        ],
        children: []
    ]
]
"""
            if discount_amount:
                condition_action_builder += f"""
def act = [
    [
        definitionId: "y_order_fixed_discount",
        parameters: [
            value: [
                type: "Map(ItemType(Currency),java.math.BigDecimal)",
                value: [ "{currency}": {discount_amount} ]
            ]
        ]
    ]
]
"""
            else:
                pct = discount_percentage or 10.0
                condition_action_builder += f"""
def act = [
    [
        definitionId: "y_order_percentage_discount",
        parameters: [
            value: [
                type: "java.math.BigDecimal",
                value: {pct}
            ]
        ]
    ]
]
"""

        elif promo_type == "ORDER_THRESHOLD_FREE_GIFT":
            thresh = threshold_amount or 500.0
            gift_sku = gift_product or "GIFT_PRODUCT"
            condition_action_builder = f"""
def cond = [
    [
        definitionId: "y_cart_total",
        parameters: [
            value: [
                type: "Map(ItemType(Currency),java.math.BigDecimal)",
                value: [ "{currency}": {thresh} ]
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
        definitionId: "y_free_gift",
        parameters: [
            product: [
                type: "ItemType(Product)",
                value: "{gift_sku}"
            ],
            quantity: [
                type: "java.lang.Integer",
                value: {gift_quantity}
            ]
        ]
    ]
]
"""

        elif promo_type == "BUNDLE_FREE_GIFT":
            gift_sku = gift_product or "GIFT_PRODUCT"
            container_items = []
            for idx, p in enumerate(qualifying_products or ["SKU1", "SKU2"]):
                container_items.append(f"""
    [
        definitionId: "y_container",
        parameters: [
            id: [
                type: "java.lang.String",
                value: "bundle_container_{idx}"
            ]
        ],
        children: [
            [
                definitionId: "y_qualifying_products",
                parameters: [
                    operator: [
                        type: "Enum(de.hybris.platform.ruledefinitions.AmountOperator)",
                        value: "GREATER_THAN_OR_EQUAL"
                    ],
                    quantity: [
                        type: "java.lang.Integer",
                        value: 1
                    ],
                    products: [
                        type: "List(ItemType(Product))",
                        value: ["{p}"]
                    ]
                ],
                children: []
            ]
        ]
    ]""")
            joined_containers = ",\n".join(container_items)
            condition_action_builder = f"""
def cond = [
{joined_containers}
]

def act = [
    [
        definitionId: "y_free_gift",
        parameters: [
            product: [
                type: "ItemType(Product)",
                value: "{gift_sku}"
            ],
            quantity: [
                type: "java.lang.Integer",
                value: {gift_quantity}
            ]
        ]
    ]
]
"""

        elif promo_type == "POTENTIAL_MESSAGE":
            min_thresh = 50.0
            target_code = target_rule_code or "target_rule"
            condition_action_builder = f"""
def cond = [
    [
        definitionId: "y_group",
        parameters: [
            operator: [
                type: "Enum(de.hybris.platform.ruleengineservices.definitions.conditions.RuleGroupOperator)",
                value: "AND"
            ]
        ],
        children: [
            [
                definitionId: "y_cart_total",
                parameters: [
                    value: [
                        type: "Map(ItemType(Currency),java.math.BigDecimal)",
                        value: [ "{currency}": {min_thresh} ]
                    ],
                    operator: [
                        type: "Enum(de.hybris.platform.ruledefinitions.AmountOperator)",
                        value: "GREATER_THAN_OR_EQUAL"
                    ]
                ],
                children: []
            ],
            [
                definitionId: "y_rule_executed",
                parameters: [
                    allowed: [
                        type: "java.lang.Boolean",
                        value: false
                    ],
                    rule: [
                        type: "ItemType(AbstractRule)",
                        value: "{target_code}"
                    ]
                ],
                children: []
            ]
        ]
    ]
]

def act = [
    [
        definitionId: "y_trigger_message",
        parameters: [:]
    ]
]
"""
        else: # Generic product discount
            prod_list = [f'"{p}"' for p in (qualifying_products or ["PRODUCT_1"])]
            pct = discount_percentage or 10.0
            condition_action_builder = f"""
def cond = [
    [
        definitionId: "y_qualifying_products",
        parameters: [
            operator: [
                type: "Enum(de.hybris.platform.ruledefinitions.AmountOperator)",
                value: "GREATER_THAN_OR_EQUAL"
            ],
            quantity: [
                type: "java.lang.Integer",
                value: 1
            ],
            products: [
                type: "List(ItemType(Product))",
                value: [{", ".join(prod_list)}]
            ]
        ],
        children: []
    ]
]

def act = [
    [
        definitionId: "y_order_percentage_discount",
        parameters: [
            value: [
                type: "java.math.BigDecimal",
                value: {pct}
            ]
        ]
    ]
]
"""

        compile_block = ""
        if compile_immediately:
            compile_block = """
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
"""

        script = f"""import de.hybris.platform.core.Registry
import de.hybris.platform.promotionengineservices.model.PromotionSourceRuleModel
import de.hybris.platform.ruleengineservices.model.RuleEngineCronJobModel
import de.hybris.platform.promotions.model.PromotionGroupModel
import de.hybris.platform.ruleengineservices.enums.RuleStatus
import groovy.json.JsonOutput

def modelService = spring.getBean("modelService")
def flexibleSearchService = spring.getBean("flexibleSearchService")
def cronJobService = spring.getBean("cronJobService")

println "=== 开始部署促销规则: {rule_code} ==="

// 1. 获取目标 PromotionGroup
def pgList = flexibleSearchService.search("SELECT {{pk}} FROM {{PromotionGroup}} WHERE {{Identifier}} = '{promo_group}'").result
def promoGroup = pgList ? pgList[0] : flexibleSearchService.search("SELECT {{pk}} FROM {{PromotionGroup}}").result[0]

// 2. 清理历史同名规则
def oldRules = flexibleSearchService.search("SELECT {{pk}} FROM {{PromotionSourceRule}} WHERE {{code}} = '{rule_code}'").result
if (oldRules) {{
    println "清理同名旧规则: " + oldRules.size() + " 条"
    modelService.removeAll(oldRules)
}}

// 3. 构建新 PromotionSourceRuleModel
def rule = modelService.create(PromotionSourceRuleModel)
rule.code = "{rule_code}"
rule.name = '{escaped_name}'
rule.description = '{escaped_desc}'
rule.priority = {priority}
rule.maxAllowedRuns = 1
rule.stackable = true
rule.status = RuleStatus.UNPUBLISHED
rule.website = promoGroup

{condition_action_builder}

rule.conditions = JsonOutput.toJson(cond)
rule.actions = JsonOutput.toJson(act)
rule.messageFired = '{escaped_msg}'
modelService.save(rule)
println "创建 PromotionSourceRuleModel 成功: " + rule.code

{compile_block}
"""
        return script
