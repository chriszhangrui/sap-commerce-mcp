import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any

class StorefrontCrawler:
    def __init__(self, client):
        self.client = client

    def fetch_products(self, site_url: str, max_products: int = 20) -> List[Dict[str, Any]]:
        """
        Attempts to fetch structured product data from a storefront URL via:
        1. Shopify public JSON API (/products.json)
        2. Schema.org JSON-LD microdata
        3. OpenGraph HTML meta tags
        """
        parsed = urllib.parse.urlparse(site_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        # 1. Try Shopify products.json
        shopify_url = f"{origin}/products.json?limit={max_products}"
        try:
            r = requests.get(shopify_url, headers=headers, timeout=10, verify=False)
            if r.status_code == 200 and "products" in r.text:
                data = r.json().get("products", [])
                if data:
                    products = []
                    for item in data[:max_products]:
                        variants = item.get("variants", [{}])
                        v0 = variants[0] if variants else {}
                        price = float(v0.get("price", 20.0))
                        img = item.get("images", [{}])[0].get("src") if item.get("images") else None
                        
                        products.append({
                            "code": re.sub(r'[^a-zA-Z0-9_-]', '_', item.get("handle") or str(item.get("id"))),
                            "name": item.get("title", "Unknown Product"),
                            "description": re.sub(r'<[^>]+>', '', item.get("body_html", "")).strip()[:500],
                            "category": item.get("product_type") or (item.get("tags") or ["Default"])[0] if isinstance(item.get("tags"), list) else "Default",
                            "price": price,
                            "image_url": img
                        })
                    return products
        except Exception:
            pass

        # 2. Try HTML scraping with JSON-LD / OpenGraph
        try:
            r = requests.get(site_url, headers=headers, timeout=10, verify=False)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                products = []
                
                # Check JSON-LD
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        js = json.loads(script.string or "{}")
                        items = js if isinstance(js, list) else [js]
                        for obj in items:
                            if obj.get("@type") == "Product":
                                offers = obj.get("offers", {})
                                if isinstance(offers, list):
                                    offers = offers[0]
                                price = float(offers.get("price", 25.0))
                                img = obj.get("image")
                                if isinstance(img, list):
                                    img = img[0]
                                code = re.sub(r'[^a-zA-Z0-9_-]', '_', obj.get("sku") or obj.get("name") or "prod")
                                products.append({
                                    "code": code,
                                    "name": obj.get("name", "Product"),
                                    "description": obj.get("description", "")[:500],
                                    "category": obj.get("category", "General"),
                                    "price": price,
                                    "image_url": img
                                })
                    except Exception:
                        continue
                if products:
                    return products[:max_products]
                
                # Fallback: OpenGraph tags for single product page
                og_title = soup.find("meta", property="og:title")
                og_image = soup.find("meta", property="og:image")
                og_desc = soup.find("meta", property="og:description")
                og_price = soup.find("meta", property="product:price:amount") or soup.find("meta", property="og:price:amount")
                
                if og_title and og_title.get("content"):
                    price = float(og_price.get("content", 30.0)) if og_price else 30.0
                    return [{
                        "code": re.sub(r'[^a-zA-Z0-9_-]', '_', og_title["content"])[:30],
                        "name": og_title["content"],
                        "description": (og_desc.get("content", "") if og_desc else "")[:500],
                        "category": "Main",
                        "price": price,
                        "image_url": og_image.get("content") if og_image else None
                    }]
        except Exception:
            pass

        return []

    def ingest_to_hybris(
        self,
        site_url: str,
        catalog_id: str = "powertoolsProductCatalog",
        max_products: int = 20,
        convert_to_b2b_cases: bool = False,
        target_currency: str = "USD",
        sync_online: bool = True,
        reindex_solr: bool = True
    ) -> str:
        """
        Crawls an external storefront, normalizes products, generates and imports ImpEx,
        synchronizes to Online, and triggers Solr indexing.
        """
        prods = self.fetch_products(site_url, max_products=max_products)
        if not prods:
            return f"❌ Could not extract any product data from '{site_url}'. Ensure the URL is accessible and contains public products/JSON-LD."

        # Process B2B case pack conversion
        categories = set()
        for p in prods:
            cat_clean = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5-]', '', p["category"]) or "General"
            p["cat_code"] = f"CAT_{cat_clean}"
            p["cat_name"] = p["category"]
            categories.add((p["cat_code"], p["cat_name"]))
            
            if convert_to_b2b_cases:
                # B2B case packaging: 24 units per box with 10% wholesale discount
                p["b2b_name"] = f"{p['name']} (Case Pack / 箱装批发)"
                p["b2b_price"] = round(p["price"] * 10 * 0.9, 2)
            else:
                p["b2b_name"] = p["name"]
                p["b2b_price"] = p["price"]

        # Build ImpEx
        lines = [
            f"# Proactive Product Ingestion from {site_url} to {catalog_id}",
            f"$productCatalog={catalog_id}",
            "$catalogVersion=catalogversion(catalog(id[default=$productCatalog]),version[default='Staged'])[unique=true,default=$productCatalog:Staged]",
            f"$curr={target_currency}",
            "",
            "# 1. Categories",
            "INSERT_UPDATE Category;code[unique=true];$catalogVersion;name[lang=zh_TW];name[lang=en]"
        ]
        for ccode, cname in categories:
            lines.append(f";{ccode};{cname};{cname}")

        lines.extend([
            "",
            "# 2. Media Assets",
            "INSERT_UPDATE Media;code[unique=true];$catalogVersion;mime[default='image/jpeg'];URL;realfilename"
        ])
        for p in prods:
            if p.get("image_url"):
                mcode = f"MED_{p['code']}"
                lines.append(f";{mcode};;{p['image_url']};{p['code']}.jpg")

        lines.extend([
            "",
            "# 3. Products",
            "INSERT_UPDATE Product;code[unique=true];$catalogVersion;name[lang=zh_TW];name[lang=en];description;picture(code,$catalogVersion);supercategories(code,$catalogVersion);unit(code)[default='pieces'];approvalStatus(code)[default='approved']"
        ])
        for p in prods:
            pic_ref = f"MED_{p['code']}" if p.get("image_url") else ""
            desc = p["description"].replace(";", ",").replace("\n", " ")
            name = p["b2b_name"].replace(";", ",")
            lines.append(f";{p['code']};;{name};{name};{desc};{pic_ref};{p['cat_code']};pieces;approved")

        lines.extend([
            "",
            "# 4. PriceRows",
            "INSERT_UPDATE PriceRow;productId[unique=true];price;currency(isocode)[unique=true];unit(code)[default='pieces'];net[default=true]"
        ])
        for p in prods:
            lines.append(f";{p['code']};{p['b2b_price']};$curr;pieces;true")

        impex_content = "\n".join(lines)
        res = self.client.import_impex(script_content=impex_content)
        status = res.get("status", "UNKNOWN")
        msg = res.get("message", "")

        out = [
            f"🛒 **Storefront Ingestion Completed:** {status}",
            f"- **Source URL:** {site_url}",
            f"- **Products Parsed & Imported:** {len(prods)}",
            f"- **Target Catalog:** `{catalog_id}:Staged`",
            f"- **Currency:** `{target_currency}`",
            f"- **B2B Wholesale Packaging Applied:** {'Yes (24罐/箱, 9折)' if convert_to_b2b_cases else 'No'}",
            f"- **Sample Imported Products:** {', '.join([p['name'][:20] for p in prods[:5]])}"
        ]

        # Automatic sync to Online
        if sync_online and status == "SUCCESS":
            from solr_sync_helper import SolrSyncHelper
            sync_helper = SolrSyncHelper(self.client)
            sync_res = sync_helper.catalog_sync(catalog_id=catalog_id, source_version="Staged", target_version="Online")
            out.append(f"\n🔄 **Catalog Synchronization to Online:**\n{sync_res}")

            if reindex_solr:
                solr_res = sync_helper.solr_reindex(mode="FULL")
                out.append(f"\n🔍 **Solr Full Reindex:**\n{solr_res}")

        return "\n".join(out)
