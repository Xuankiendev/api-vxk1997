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

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    url = params["url"]
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
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
        
        headers = dict(response.headers)
        
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
        if 'react' in response.text.lower():
            technologies.append('React')
        if 'vue' in response.text.lower():
            technologies.append('Vue.js')
        if 'angular' in response.text.lower():
            technologies.append('Angular')
        if 'jquery' in response.text.lower():
            technologies.append('jQuery')
        if 'bootstrap' in response.text.lower():
            technologies.append('Bootstrap')
        if 'tailwind' in response.text.lower():
            technologies.append('Tailwind CSS')
        if 'wordpress' in response.text.lower():
            technologies.append('WordPress')
        if 'shopify' in response.text.lower():
            technologies.append('Shopify')
        
        social_media_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(social in href for social in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'tiktok.com']):
                social_media_links.append(link['href'])
        
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
            "headers": headers,
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
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
