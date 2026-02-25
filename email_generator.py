#!/usr/bin/env python3
"""
Corporate Email Pattern Generator

Features:
- Reads names from .txt
- Generates multiple email patterns
- Custom domain support
- Duplicate removal
- Clean output file

Usage:
python email_generator.py -i names.txt -d company.com -o emails.txt
"""

import argparse
import re


def clean_name(name: str):
    """Normalize and split name."""
    name = name.strip().lower()
    name = re.sub(r'[^a-z\s]', '', name)  # remove special chars
    parts = name.split()

    if len(parts) == 0:
        return None, None
    if len(parts) == 1:
        return parts[0], ""

    return parts[0], parts[-1]


def generate_patterns(first, last, domain):
    """Generate common corporate email patterns."""
    emails = set()

    if not first:
        return emails

    # If no last name
    if not last:
        emails.add(f"{first}@{domain}")
        return emails

    fi = first[0]
    li = last[0]

    patterns = [
        f"{first}@{domain}",
        f"{last}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{fi}{last}@{domain}",
        f"{first}{li}@{domain}",
        f"{first}_{last}@{domain}",
        f"{first}-{last}@{domain}",
        f"{fi}.{last}@{domain}",
        f"{first}.{li}@{domain}",
    ]

    emails.update(patterns)
    return emails


def main():
    parser = argparse.ArgumentParser(description="Email Pattern Generator")
    parser.add_argument("-i", "--input", required=True, help="Input names file")
    parser.add_argument("-d", "--domain", required=True, help="Company domain")
    parser.add_argument("-o", "--output", default="generated_emails.txt",
                        help="Output file")

    args = parser.parse_args()

    all_emails = set()

    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            first, last = clean_name(line)
            if first:
                emails = generate_patterns(first, last, args.domain)
                all_emails.update(emails)

    # Save output
    with open(args.output, "w", encoding="utf-8") as f:
        for email in sorted(all_emails):
            f.write(email + "\n")

    print(f"[+] Generated {len(all_emails)} unique emails")
    print(f"[+] Saved to {args.output}")


if __name__ == "__main__":
    main()
