from sqlalchemy.orm import Session
from ..auth import validateApiKey
import requests
from urllib.parse import urlparse
import socket
from bs4 import BeautifulSoup
import dns.resolver
import whois
import ssl
import datetime
from ipwhois import IPWhois
import random
import time

PROXY_APIS = [
    "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

def get_proxy_list():
    proxies = []
    for api_url in PROXY_APIS:
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                proxy_text = response.text.strip()
                for line in proxy_text.split('\n'):
                    line = line.strip()
                    if ':' in line and len(line.split(':')) == 2:
                        ip, port = line.split(':')
                        if ip and port.isdigit():
                            proxies.append(f"http://{ip}:{port}")
            if len(proxies) >= 50:
                break
        except:
            continue
    return proxies

def parse_set_cookie_header(set_cookie_header):
    cookies = {}
    if not set_cookie_header:
        return cookies
    
    cookie_parts = set_cookie_header.split(', ')
    current_cookie = ""
    
    for part in cookie_parts:
        if '=' in part and not any(attr in part.lower() for attr in ['expires=', 'max-age=', 'domain=', 'path=', 'secure', 'httponly', 'samesite=']):
            if current_cookie:
                cookie_name_value = current_cookie.split(';')[0].strip()
                if '=' in cookie_name_value:
                    name, value = cookie_name_value.split('=', 1)
                    cookies[name.strip()] = value.strip()
            current_cookie = part
        else:
            current_cookie += ", " + part
    
    if current_cookie:
        cookie_name_value = current_cookie.split(';')[0].strip()
        if '=' in cookie_name_value:
            name, value = cookie_name_value.split('=', 1)
            cookies[name.strip()] = value.strip()
    
    return cookies

def make_request_with_retry(url, headers, cookies=None, max_retries=10):
    session = requests.Session()
    session.headers.update(headers)
    
    if cookies:
        session.cookies.update(cookies)
    
    try:
        response = session.get(url, timeout=15, allow_redirects=True)
        
        extracted_cookies = {}
        set_cookie_header = response.headers.get('Set-Cookie')
        if set_cookie_header:
            extracted_cookies = parse_set_cookie_header(set_cookie_header)
            session.cookies.update(extracted_cookies)
        
        if response.status_code == 403:
            raise requests.exceptions.HTTPError("403 Forbidden")
        
        response._extracted_cookies = extracted_cookies
        return response
        
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        if "403" in str(e) or "Forbidden" in str(e):
            proxies = get_proxy_list()
            if not proxies:
                raise Exception("No proxies available")
            
            random.shuffle(proxies)
            
            for attempt in range(min(max_retries, len(proxies))):
                try:
                    proxy = proxies[attempt]
                    proxy_dict = {
                        'http': proxy,
                        'https': proxy
                    }
                    
                    time.sleep(random.uniform(1, 3))
                    
                    response = session.get(
                        url, 
                        timeout=20, 
                        allow_redirects=True, 
                        proxies=proxy_dict
                    )
                    
                    extracted_cookies = {}
                    set_cookie_header = response.headers.get('Set-Cookie')
                    if set_cookie_header:
                        extracted_cookies = parse_set_cookie_header(set_cookie_header)
                        session.cookies.update(extracted_cookies)
                    
                    if response.status_code != 403:
                        response._extracted_cookies = extracted_cookies
                        response._proxy_used = True
                        return response
                        
                except:
                    continue
            
            raise Exception(f"All proxy attempts failed after {max_retries} tries")
        else:
            raise e

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    url = params["url"]
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        headers = get_random_headers()
        
        cookies = {}
        if params.get("cookies"):
            if isinstance(params["cookies"], dict):
                cookies = params["cookies"]
            elif isinstance(params["cookies"], str):
                for cookie in params["cookies"].split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies[key] = value
        
        response = make_request_with_retry(url, headers, cookies)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch URL. Status code: {response.status_code}"}
        
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        
        try:
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip_address = "Unknown"
        
        dns_info = {}
        try:
            dns_records = {}
            for record_type in ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS']:
                try:
                    answers = dns.resolver.resolve(hostname, record_type)
                    dns_records[record_type] = [str(answer) for answer in answers]
                except:
                    dns_records[record_type] = []
            dns_info = dns_records
        except:
            dns_info = {}
        
        hosting_provider = "Unknown"
        cdn_provider = "Unknown"
        try:
            if ip_address != "Unknown":
                obj = IPWhois(ip_address)
                result = obj.lookup_rdap()
                hosting_provider = result.get('network', {}).get('name', 'Unknown')
                
                server_header = response.headers.get('server', '').lower()
                cf_ray = response.headers.get('cf-ray')
                if cf_ray or 'cloudflare' in server_header:
                    cdn_provider = "Cloudflare"
                elif 'fastly' in server_header:
                    cdn_provider = "Fastly"
                elif 'amazonaws' in hosting_provider.lower():
                    cdn_provider = "AWS CloudFront"
                elif 'google' in hosting_provider.lower():
                    cdn_provider = "Google Cloud CDN"
                elif 'microsoft' in hosting_provider.lower():
                    cdn_provider = "Azure CDN"
                elif response.headers.get('x-served-by'):
                    cdn_provider = "Varnish/Custom CDN"
                
                if 'github' in hosting_provider.lower() or 'github.io' in hostname:
                    hosting_provider = "GitHub Pages"
                elif 'vercel' in hosting_provider.lower() or 'vercel.app' in hostname:
                    hosting_provider = "Vercel"
                elif 'netlify' in hosting_provider.lower() or 'netlify.app' in hostname:
                    hosting_provider = "Netlify"
                elif 'heroku' in hosting_provider.lower() or 'herokuapp.com' in hostname:
                    hosting_provider = "Heroku"
                elif 'firebase' in hostname or 'firebaseapp.com' in hostname:
                    hosting_provider = "Firebase"
        except:
            pass
        
        domain_info = {}
        try:
            w = whois.whois(hostname)
            domain_info = {
                "registrar": w.registrar,
                "creation_date": str(w.creation_date) if w.creation_date else None,
                "expiration_date": str(w.expiration_date) if w.expiration_date else None,
                "updated_date": str(w.updated_date) if w.updated_date else None,
                "name_servers": w.name_servers if w.name_servers else []
            }
        except:
            domain_info = {}
        
        ssl_info = {}
        if url.startswith('https://'):
            try:
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443)) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        ssl_info = {
                            "issuer": dict(x[0] for x in cert['issuer']),
                            "subject": dict(x[0] for x in cert['subject']),
                            "version": cert['version'],
                            "serial_number": cert['serialNumber'],
                            "not_before": cert['notBefore'],
                            "not_after": cert['notAfter'],
                            "signature_algorithm": cert.get('signatureAlgorithm', 'Unknown')
                        }
            except:
                ssl_info = {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '').strip() if meta_description else ""
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = meta_keywords.get('content', '').strip() if meta_keywords else ""
        
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                meta_tags[meta.get('name')] = meta.get('content', '')
            elif meta.get('property'):
                meta_tags[meta.get('property')] = meta.get('content', '')
        
        headers_response = dict(response.headers)
        
        cache_info = {
            "has_cache_control": bool(response.headers.get('cache-control')),
            "cache_control": response.headers.get('cache-control', ''),
            "etag": response.headers.get('etag', ''),
            "expires": response.headers.get('expires', ''),
            "last_modified": response.headers.get('last-modified', ''),
            "age": response.headers.get('age', ''),
            "vary": response.headers.get('vary', ''),
            "pragma": response.headers.get('pragma', '')
        }
        
        security_headers = {
            "strict_transport_security": response.headers.get('strict-transport-security', ''),
            "content_security_policy": response.headers.get('content-security-policy', ''),
            "x_frame_options": response.headers.get('x-frame-options', ''),
            "x_content_type_options": response.headers.get('x-content-type-options', ''),
            "referrer_policy": response.headers.get('referrer-policy', ''),
            "permissions_policy": response.headers.get('permissions-policy', '')
        }
        
        has_js = bool(soup.find_all('script'))
        has_forms = bool(soup.find_all('form'))
        has_ajax_indicators = any([
            'XMLHttpRequest' in response.text,
            'fetch(' in response.text,
            'axios' in response.text,
            'jQuery.ajax' in response.text,
            '$.ajax' in response.text
        ])
        
        is_dynamic = has_js or has_forms or has_ajax_indicators
        
        links = []
        for link in soup.find_all('a', href=True):
            links.append(link['href'])
        
        images = []
        for img in soup.find_all('img', src=True):
            images.append(img['src'])
        
        stylesheets = []
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                stylesheets.append(link['href'])
        
        scripts = []
        for script in soup.find_all('script', src=True):
            scripts.append(script['src'])
        
        technologies = []
        response_text_lower = response.text.lower()
        if 'react' in response_text_lower:
            technologies.append('React')
        if 'vue' in response_text_lower:
            technologies.append('Vue.js')
        if 'angular' in response_text_lower:
            technologies.append('Angular')
        if 'jquery' in response_text_lower:
            technologies.append('jQuery')
        if 'bootstrap' in response_text_lower:
            technologies.append('Bootstrap')
        if 'tailwind' in response_text_lower:
            technologies.append('Tailwind CSS')
        if 'wordpress' in response_text_lower:
            technologies.append('WordPress')
        if 'shopify' in response_text_lower:
            technologies.append('Shopify')
        
        social_media_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(social in href for social in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'tiktok.com']):
                social_media_links.append(link['href'])
        
        extracted_cookies = getattr(response, '_extracted_cookies', {})
        
        return {
            "url": response.url,
            "original_url": params["url"],
            "status_code": response.status_code,
            "title": title_text,
            "description": description,
            "keywords": keywords,
            "hostname": hostname,
            "ip_address": ip_address,
            "hosting_provider": hosting_provider,
            "cdn_provider": cdn_provider,
            "dns_records": dns_info,
            "domain_info": domain_info,
            "ssl_info": ssl_info,
            "is_dynamic": is_dynamic,
            "website_type": "Dynamic" if is_dynamic else "Static",
            "has_javascript": has_js,
            "has_forms": has_forms,
            "content_length": len(response.content),
            "content_type": response.headers.get('content-type', ''),
            "encoding": response.encoding,
            "headers": headers_response,
            "cache_info": cache_info,
            "security_headers": security_headers,
            "meta_tags": meta_tags,
            "links_count": len(links),
            "images_count": len(images),
            "stylesheets_count": len(stylesheets),
            "scripts_count": len(scripts),
            "links": links[:50],
            "images": images[:20],
            "stylesheets": stylesheets[:10],
            "scripts": scripts[:10],
            "social_media_links": social_media_links,
            "detected_technologies": technologies,
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "redirected": response.url != url,
            "final_url": response.url if response.url != url else None,
            "timestamp": datetime.datetime.now().isoformat(),
            "cookies_used": len(cookies) > 0,
            "extracted_cookies": extracted_cookies,
            "has_cf_bm": "__cf_bm" in extracted_cookies,
            "has_cfuid": "__cf_uid" in extracted_cookies,
            "has_cloudflare_cookies": any(key.startswith('_cf') or 'cloudflare' in key.lower() for key in extracted_cookies.keys()),
            "proxy_used": hasattr(response, '_proxy_used') or False
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
