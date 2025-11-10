import dns.resolver
import sys
from urllib.parse import urlparse

def get_domain_from_url(url):
    """Extract domain from URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain

def check_dmarc_record(domain):
    """Check if DMARC record exists for the domain"""
    try:
        # DMARC records are stored in _dmarc subdomain
        dmarc_domain = f'_dmarc.{domain}'
        
        # Query TXT records for _dmarc.domain
        answers = dns.resolver.resolve(dmarc_domain, 'TXT')
        
        dmarc_records = []
        for rdata in answers:
            for txt_string in rdata.strings:
                txt_string = txt_string.decode('utf-8')
                if txt_string.startswith('v=DMARC1'):
                    dmarc_records.append(txt_string)
        
        return dmarc_records if dmarc_records else None
        
    except dns.resolver.NXDOMAIN:
        return None  # No DMARC record found
    except dns.resolver.NoAnswer:
        return None  # No TXT records found
    except dns.resolver.Timeout:
        return "timeout"
    except Exception as e:
        return f"error: {str(e)}"

def main():
    print("DMARC Record Checker")
    print("===================")
    
    if len(sys.argv) > 1:
        # Get domain from command line argument
        input_domain = sys.argv[1]
    else:
        # Interactive input
        input_domain = input("Enter website URL or domain: ").strip()
    
    if not input_domain:
        print("Error: No domain provided")
        return
    
    # Extract domain from URL if necessary
    domain = get_domain_from_url(input_domain)
    
    print(f"\nChecking DMARC record for: {domain}")
    print("Please wait...")
    
    # Check DMARC record
    result = check_dmarc_record(domain)
    
    print("\n" + "="*50)
    
    if result == "timeout":
        print("Error: DNS query timed out")
    elif result and isinstance(result, str) and result.startswith("error:"):
        print(f"Error: {result}")
    elif result:
        print("✅ DMARC Record FOUND")
        print("\nDMARC Record(s):")
        for i, record in enumerate(result, 1):
            print(f"{i}. {record}")
    else:
        print("❌ No DMARC Record Found")
        print("\nThis domain does not have a DMARC record configured.")
        print("DMARC helps prevent email spoofing and phishing attacks.")

if __name__ == "__main__":
    main()
