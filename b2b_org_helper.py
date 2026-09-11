import json
import re
from typing import Optional, List, Dict, Any

def normalize_lang(lang: str) -> str:
    l = lang.replace("-", "_").strip()
    if l.lower() in ["zh_cn", "zh-cn", "zh_hans", "zh_hans_cn"]:
        return "zh"
    return l

class B2BOrgHelper:
    def __init__(self, client):
        self.client = client

    def _generate_realistic_hierarchy(self, root_id: str, root_name: str, languages: List[str]):
        """
        Generates realistic, industry-appropriate organizational units and names
        tailored to the customer domain with full multi-language translations.
        """
        name_lower = root_name.lower()
        
        # Medical / Healthcare (e.g. Mindray, Medtronic, etc.)
        if any(k in name_lower for k in ["医", "药", "med", "health", "bio", "clinic"]):
            unit1_id = f"{root_id}_DEVICES"
            unit1_zh = f"{root_name} - 医疗设备与核心耗材采购部"
            unit1_tw = f"{root_name} - 醫療設備與核心耗材採購部"
            unit1_en = f"{root_name} - Medical Devices & Consumables Div"
            
            unit2_id = f"{root_id}_SUPPLY"
            unit2_zh = f"{root_name} - 诊断试剂与供应链协同中心"
            unit2_tw = f"{root_name} - 診斷試劑與供應鏈協同中心"
            unit2_en = f"{root_name} - Diagnostics & Supply Chain Center"
            
            budget_zh = f"{root_name} - 医疗设备与耗材年度集采专项预算"
            budget_tw = f"{root_name} - 醫療設備與耗材年度集採專項預算"
            budget_en = f"{root_name} - Annual Medical Sourcing Strategic Budget"
            
            approver_name = f"{root_name} 战略采购总监 (李明) / Director Ming Li"
            buyer_name = f"{root_name} 资深采购经理 (王浩) / Manager Hao Wang"

        # Tech / Electronics / Hardware (e.g. Anker, DJI, Lenovo, etc.)
        elif any(k in name_lower for k in ["电", "科技", "tech", "elec", "smart", "ai", "cloud"]):
            unit1_id = f"{root_id}_COMPONENTS"
            unit1_zh = f"{root_name} - 核心元器件战略采控部"
            unit1_tw = f"{root_name} - 核心元器件戰略採控部"
            unit1_en = f"{root_name} - Strategic Electronic Components Div"
            
            unit2_id = f"{root_id}_GLOBAL_OPS"
            unit2_zh = f"{root_name} - 海外分销渠道与智能硬件运营部"
            unit2_tw = f"{root_name} - 海外分銷渠道與智能硬件運營部"
            unit2_en = f"{root_name} - Global Distribution & Smart Hardware Div"
            
            budget_zh = f"{root_name} - 全球智能硬件采购战略专项预算"
            budget_tw = f"{root_name} - 全球智能硬件採購戰略專項預算"
            budget_en = f"{root_name} - Global Smart Hardware Strategic Budget"
            
            approver_name = f"{root_name} 供应链采控总监 (张伟) / VP Wei Zhang"
            buyer_name = f"{root_name} 海外渠道采购专员 (刘洋) / Lead Yang Liu"

        # Industrial / Manufacturing / Machinery (e.g. Bosch, Siemens, etc.)
        elif any(k in name_lower for k in ["工", "制造", "机械", "auto", "machin", "manuf", "steel"]):
            unit1_id = f"{root_id}_MATERIALS"
            unit1_zh = f"{root_name} - 工业装备与原材料采购部"
            unit1_tw = f"{root_name} - 工業裝備與原材料採購部"
            unit1_en = f"{root_name} - Industrial Equipment & Raw Materials Div"
            
            unit2_id = f"{root_id}_FACILITIES"
            unit2_zh = f"{root_name} - 区域精密制造与备件供应链中心"
            unit2_tw = f"{root_name} - 區域精密製造與備件供應鏈中心"
            unit2_en = f"{root_name} - Regional Precision Mfg & Spare Parts Hub"
            
            budget_zh = f"{root_name} - 精密制造与工业物资采购预算"
            budget_tw = f"{root_name} - 精密製造與工業物資採購預算"
            budget_en = f"{root_name} - Industrial Materials & MRO Budget"
            
            approver_name = f"{root_name} 物资采控总监 (赵强) / Director Qiang Zhao"
            buyer_name = f"{root_name} 工业品采购主管 (陈曦) / Specialist Xi Chen"

        # General Enterprise / Retail / FMCG / Consumer
        else:
            unit1_id = f"{root_id}_SOURCING"
            unit1_zh = f"{root_name} - 战略物资统采事业部"
            unit1_tw = f"{root_name} - 戰略物資統採事業部"
            unit1_en = f"{root_name} - Strategic Direct Sourcing Div"
            
            unit2_id = f"{root_id}_REGIONAL"
            unit2_zh = f"{root_name} - 区域分销与渠道采控中心"
            unit2_tw = f"{root_name} - 區域分銷與渠道採控中心"
            unit2_en = f"{root_name} - Regional Distribution & Sourcing Center"
            
            budget_zh = f"{root_name} - 年度企业综合业务采购预算"
            budget_tw = f"{root_name} - 年度企業綜合業務採購預算"
            budget_en = f"{root_name} - Corporate Annual Procurement Budget"
            
            approver_name = f"{root_name} 集团采购总监 (周峰) / Director Feng Zhou"
            buyer_name = f"{root_name} 采购运营主管 (林悦) / Supervisor Yue Lin"

        sub_units = [
            {
                "id": unit1_id,
                "name": unit1_en,
                "translations": {"en": unit1_en, "zh": unit1_zh, "zh_TW": unit1_tw}
            },
            {
                "id": unit2_id,
                "name": unit2_en,
                "translations": {"en": unit2_en, "zh": unit2_zh, "zh_TW": unit2_tw}
            }
        ]
        
        root_trans = {
            "en": f"{root_name} Corporate Procurement HQ",
            "zh": f"{root_name} 集团全球采购与供应链总部",
            "zh_TW": f"{root_name} 集團全球採購與供應鏈總部"
        }
        
        budget_trans = {"en": budget_en, "zh": budget_zh, "zh_TW": budget_tw}

        return {
            "root_trans": root_trans,
            "sub_units": sub_units,
            "budget_trans": budget_trans,
            "approver_name": approver_name,
            "buyer_name": buyer_name
        }

    def scaffold_org(
        self,
        root_unit_id: str,
        root_unit_name: str,
        sub_units: Optional[List[Dict[str, Any]]] = None,
        currency: str = "USD",
        languages: Optional[List[str]] = None,
        monthly_budget: float = 50000.0,
        approval_threshold: float = 200.0,
        buyer_name: Optional[str] = None,
        buyer_email: Optional[str] = None,
        approver_name: Optional[str] = None,
        approver_email: Optional[str] = None,
        default_password: str = "nimda"
    ) -> str:
        raw_langs = languages or ["en", "zh", "zh_TW"]
        langs = []
        for l in raw_langs:
            nl = normalize_lang(l)
            if nl not in langs:
                langs.append(nl)

        meta = self._generate_realistic_hierarchy(root_unit_id, root_unit_name, langs)

        final_sub_units = sub_units or meta["sub_units"]
        app_name = approver_name or meta["approver_name"]
        buy_name = buyer_name or meta["buyer_name"]
        
        clean_root_id = re.sub(r"[^a-zA-Z0-9_]", "_", root_unit_id.strip()).upper()
        buyer = buyer_email or f"buyer.{clean_root_id.lower()}@demo.com"
        approver = approver_email or f"approver.{clean_root_id.lower()}@demo.com"
        perm_code = f"{clean_root_id}_Threshold_Perm"

        # Build dynamic ImpEx headers matching requested normalized languages
        unit_loc_headers = ";".join([f"locName[lang={l}]" for l in langs])
        cc_name_headers = ";".join([f"name[lang={l}]" for l in langs])
        budget_name_headers = ";".join([f"name[lang={l}]" for l in langs])

        # 1. Root & Sub Units
        lines = [
            f"# ====================================================================",
            f"# Realistic B2B Organization Scaffold for {root_unit_name} ({clean_root_id})",
            f"# Supported Languages: {', '.join(langs)} | Currency: {currency}",
            f"# ====================================================================",
            "$defaultPassword = " + default_password,
            "$curr = " + currency,
            "",
            "# 1. Organization Units (B2BUnit)",
            f"INSERT_UPDATE B2BUnit;uid[unique=true];name;{unit_loc_headers};groups(uid);active[default=true]"
        ]

        # Root row
        root_vals = ";".join([meta["root_trans"].get(l, root_unit_name) for l in langs])
        lines.append(f";{clean_root_id};{meta['root_trans'].get('en', root_unit_name)};{root_vals};b2bgroup;true")

        # Sub-units rows
        for su in final_sub_units:
            su_id = su["id"]
            trans = su.get("translations", {})
            su_vals = ";".join([trans.get(l, su.get("name", su_id)) for l in langs])
            lines.append(f";{su_id};{su.get('name', su_id)};{su_vals};{clean_root_id};true")

        # 2. Budget and Cost Centers
        budget_vals = ";".join([meta["budget_trans"].get(l, f"{root_unit_name} Budget") for l in langs])
        lines.extend([
            "",
            "# 2. Budgets & Cost Centers",
            f"INSERT_UPDATE B2BBudget;code[unique=true];Unit(uid);budget;currency(isocode);dateRange[dateformat=dd.MM.yyyy hh:mm:ss,allownull=true];{budget_name_headers};active[default=true]",
            f";{clean_root_id}_Budget;{clean_root_id};{monthly_budget};$curr;01.01.2025 00:00:00,31.12.2030 23:59:59;{budget_vals};true",
            "",
            f"INSERT_UPDATE B2BCostCenter;code[unique=true];Unit(uid);currency(isocode);budgets(code);{cc_name_headers};active[default=true]"
        ])

        for su in final_sub_units:
            su_id = su["id"]
            cc_code = f"CC_{su_id}"
            trans = su.get("translations", {})
            cc_vals = ";".join([f"{trans.get(l, su_id)} Cost Center" if l == "en" else f"{trans.get(l, su_id)} 专属成本中心" for l in langs])
            lines.append(f";{cc_code};{su_id};$curr;{clean_root_id}_Budget;{cc_vals};true")

        # 3. Permissions
        lines.extend([
            "",
            "# 3. Approval Rules",
            f"INSERT_UPDATE B2BOrderThresholdPermission;code[unique=true];Unit(uid);threshold;currency(isocode);active[default=true]",
            f";{perm_code};{clean_root_id};{approval_threshold};$curr;true",
            "",
            "# 4. Personnel (Approver & Buyer)",
            "INSERT_UPDATE B2BCustomer;uid[unique=true];name;email;customerID;defaultB2BUnit(uid);groups(uid);password[default=$defaultPassword];active[default=true]",
            f";{approver};{app_name};{approver};{approver};{clean_root_id};b2bgroup,b2bapprovergroup,b2bmanagergroup;;true",
            f";{buyer};{buy_name};{buyer};{buyer};{final_sub_units[0]['id']};b2bgroup,b2bcustomergroup,unitorderviewergroup;;true",
            "",
            "UPDATE B2BCustomer;uid[unique=true];permissions(code,Unit(uid));approvers(uid)",
            f";{buyer};{perm_code}:{clean_root_id};{approver}"
        ])

        impex_content = "\n".join(lines)
        res = self.client.import_impex(script_content=impex_content)
        status = res.get("status", "UNKNOWN")
        msg = res.get("message", "")
        dump = res.get("dump", "")

        out = [
            f"🏢 **B2B 真实组织架构构建结果 (Status: {status})**",
            f"- **组织全称:** `{root_unit_name}` (根节点: `{clean_root_id}`)",
            f"- **下辖业务部门 / 事业部:**",
        ]
        for su in final_sub_units:
            trans = su.get("translations", {})
            zh_name = trans.get("zh", su.get("name", ""))
            en_name = trans.get("en", su.get("name", ""))
            out.append(f"  • `{su['id']}`: {zh_name} ({en_name})")

        out.extend([
            f"- **预算与成本中心:** 月度额度 `{monthly_budget} {currency}`，已挂载至各事业部专属成本中心",
            f"- **审批控制限额:** 单笔采购超过 `{approval_threshold} {currency}` 自动拦截并触发上级审批",
            f"- **采购总监/审批人:** `{approver}` ({app_name}) | 初始密码: `{default_password}`",
            f"- **高级采购经理/买家:** `{buyer}` ({buy_name}) | 初始密码: `{default_password}`",
            f"- **多语言注入:** 已同步补齐 {', '.join(langs)} 本地化字段"
        ])
        if dump:
            out.append(f"\n**导入日志 / 详情:**\n```\n{dump}\n```")
        return "\n".join(out)

    def diagnose_user_org(self, user_uid: str, lang: str = "zh") -> str:
        """
        Diagnoses a B2B user's organizational context with language-aligned output.
        """
        groovy_script = f"""
import de.hybris.platform.b2b.model.B2BCustomerModel
import de.hybris.platform.b2b.model.B2BUnitModel
import de.hybris.platform.b2b.model.B2BBudgetModel
import de.hybris.platform.core.model.c2l.CurrencyModel
import de.hybris.platform.servicelayer.search.FlexibleSearchQuery

def uid = "{user_uid}"
def isZh = "{lang}".toLowerCase().startsWith("zh")

if (isZh) {{
    println "🏢 === B2B 组织架构与账号结算权限深度体检: [${{uid}}] ==="
}} else {{
    println "🏢 === B2B Organization & Checkout Permissions Doctor: [${{uid}}] ==="
}}

def uQuery = new FlexibleSearchQuery("SELECT {{pk}} FROM {{B2BCustomer}} WHERE {{uid}}=?uid")
uQuery.addQueryParameter("uid", uid)
def users = flexibleSearchService.search(uQuery).result

if (!users) {{
    println isZh ? "❌ 数据库中未找到用户 [${{uid}}]！" : "❌ User [${{uid}}] not found in B2BCustomer database!"
    return
}}

B2BCustomerModel user = users[0]
println isZh ? "✅ 用户身份: ${{user.name ?: user.uid}} (激活状态: ${{user.active}})" : "✅ User Found: ${{user.name ?: user.uid}} (active: ${{user.active}})"
println isZh ? "   关联安全用户组: ${{user.groups*.uid.join(', ')}}" : "   Assigned User Groups: ${{user.groups*.uid.join(', ')}}"

// Check B2B Unit
B2BUnitModel unit = user.defaultB2BUnit
if (!unit) {{
    println isZh ? "❌ [组织机构] 该买家未挂载任何 defaultB2BUnit 归属部门！" : "❌ [B2BUnit] User has NO defaultB2BUnit assigned!"
    return
}}
println isZh ? "✅ [所属机构] 归属部门: ${{unit.uid}} - ${{unit.locName ?: unit.name}} (状态: ${{unit.active}})" : "✅ [B2BUnit] Default Unit: ${{unit.uid}} - ${{unit.name}} (active: ${{unit.active}})"

// Check Cost Centers
def ccQuery = new FlexibleSearchQuery("SELECT {{pk}} FROM {{B2BCostCenter}} WHERE {{unit}}=?unit AND {{active}}=true")
ccQuery.addQueryParameter("unit", unit)
def costCenters = flexibleSearchService.search(ccQuery).result

if (costCenters) {{
    costCenters.each {{ cc ->
        println isZh ? "✅ [成本中心] 可用 CC: ${{cc.code}} - ${{cc.name}} (币种: ${{cc.currency?.isocode}})" : "✅ [CostCenter] Active CC: ${{cc.code}} - ${{cc.name}} (currency: ${{cc.currency?.isocode}})"
        if (cc.budgets) {{
            cc.budgets.each {{ B2BBudgetModel b ->
                println isZh ? "   └─ [关联预算] ${{b.code}}: ${{b.budget}} ${{b.currency?.isocode}} (状态: ${{b.active}})" : "   └─ [Budget] ${{b.code}}: ${{b.budget}} ${{b.currency?.isocode}} (Active: ${{b.active}})"
            }}
        }} else {{
            println isZh ? "   ⚠️ [关联预算] 成本中心 ${{cc.code}} 未绑定任何有效预算！" : "   ⚠️ [Budget] No budgets attached to Cost Center ${{cc.code}}!"
        }}
    }}
}} else {{
    println isZh ? "⚠️ [成本中心] 部门 '${{unit.uid}}' 下未检索到有效成本中心（结账时将缺少 Cost Center 选项）！" : "⚠️ [CostCenter] No active Cost Centers assigned directly to Unit '${{unit.uid}}'!"
}}

// Check Approvers & Permissions
println isZh ? "📋 [审批链与权限控制]:" : "📋 [Approval Chain & Permission Control]:"
if (user.approvers) {{
    println isZh ? "✅ 指定直属审批人: ${{user.approvers.collect {{ it.name + ' (' + it.uid + ')' }}.join(', ')}}" : "✅ Assigned Approvers: ${{user.approvers.collect {{ it.name + ' (' + it.uid + ')' }}.join(', ')}}"
}} else {{
    println isZh ? "⚠️ 未配置任何审批人账号！" : "⚠️ No assigned Approvers for this user!"
}}

if (user.permissions) {{
    user.permissions.each {{ perm ->
        println isZh ? "✅ 订单审批限额规则: ${{perm.code}} (${{perm.itemtype}})" : "✅ Permission Rule: ${{perm.code}} (${{perm.itemtype}})"
    }}
}} else {{
    println isZh ? "ℹ️ 无特定金额审批规则限制（订单下单时可能不会被拦截审批）。" : "ℹ️ No specific order threshold permissions (Orders may not require approval)."
}}

println isZh ? "\\n🩺 诊断检查完成！" : "\\n🩺 Diagnosis complete!"
"""
        res = self.client.execute_groovy(script=groovy_script, commit=False)
        out = res.get("outputText", "").strip()
        stack = res.get("stacktraceText", "").strip()
        if stack:
            return f"{out}\n\n⚠️ Error during diagnosis:\n{stack}" if out else stack
        return out
