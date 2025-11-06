#!/bin/bash

# Subdomain Finder Tool for Kali Linux
# Author: Auto-generated
# Description: Comprehensive subdomain enumeration tool with waybackurls

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}"
echo "   _____       __      __                 _           "
echo "  / ___/____  / /_  __/ /_  ___  _____  (_)________ _"
echo "  \__ \/ __ \/ / / / / __ \/ _ \/ ___/ / / ___/ __  /"
echo " ___/ / /_/ / / /_/ / /_/ /  __/ /  / / / /__/ /_/ / "
echo "/____/\____/_/\__, /_.___/\___/_/  /_/_/\___/\__,_/  "
echo "             /____/                                  "
echo -e "${NC}"
echo -e "${BLUE}Subdomain Finder Tool for Kali Linux${NC}"
echo -e "${PURPLE}With WaybackURLs Integration${NC}"
echo "=========================================="

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to install dependencies
install_dependencies() {
    echo -e "${YELLOW}[!] Checking and installing dependencies...${NC}"
    
    # Check and install golang
    if ! command_exists go; then
        echo -e "${YELLOW}[!] Installing Golang...${NC}"
        sudo apt update && sudo apt install golang -y
    else
        echo -e "${GREEN}[+] Golang is already installed${NC}"
    fi
    
    # Setup Go environment
    if [ -n "$BASH_VERSION" ]; then
        if ! grep -q "export GOPATH=\$HOME/go" ~/.bashrc; then
            echo 'export GOPATH=$HOME/go' >> ~/.bashrc
            echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc
        fi
        source ~/.bashrc
    fi
    
    if [ -n "$ZSH_VERSION" ]; then
        if ! grep -q "export GOPATH=\$HOME/go" ~/.zshrc; then
            echo 'export GOPATH=$HOME/go' >> ~/.zshrc
            echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.zshrc
        fi
        source ~/.zshrc
    fi
    
    # Install subfinder
    if ! command_exists subfinder; then
        echo -e "${YELLOW}[!] Installing subfinder...${NC}"
        go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    else
        echo -e "${GREEN}[+] subfinder is already installed${NC}"
    fi
    
    # Install assetfinder
    if ! command_exists assetfinder; then
        echo -e "${YELLOW}[!] Installing assetfinder...${NC}"
        go install github.com/tomnomnom/assetfinder@latest
    else
        echo -e "${GREEN}[+] assetfinder is already installed${NC}"
    fi
    
    # Install httprobe
    if ! command_exists httprobe; then
        echo -e "${YELLOW}[!] Installing httprobe...${NC}"
        go install github.com/tomnomnom/httprobe@latest
    else
        echo -e "${GREEN}[+] httprobe is already installed${NC}"
    fi
    
    # Install waybackurls
    if ! command_exists waybackurls; then
        echo -e "${YELLOW}[!] Installing waybackurls...${NC}"
        go install github.com/tomnomnom/waybackurls@latest
    else
        echo -e "${GREEN}[+] waybackurls is already installed${NC}"
    fi
    
    # Install findomain
    if ! command_exists findomain; then
        echo -e "${YELLOW}[!] Installing findomain...${NC}"
        sudo apt install findomain -y
    else
        echo -e "${GREEN}[+] findomain is already installed${NC}"
    fi
    
    # Install sublist3r
    if ! command_exists sublist3r; then
        echo -e "${YELLOW}[!] Installing sublist3r...${NC}"
        sudo apt install sublist3r -y
    else
        echo -e "${GREEN}[+] sublist3r is already installed${NC}"
    fi
    
    echo -e "${GREEN}[+] All dependencies checked and installed!${NC}"
}

# Function to run subdomain enumeration
run_enumeration() {
    local target=$1
    local output_dir=$2
    
    echo -e "${BLUE}[*] Starting subdomain enumeration for: $target${NC}"
    
    # Create temporary directory
    mkdir -p "$output_dir/temp"
    
    # Run subfinder
    echo -e "${YELLOW}[!] Running subfinder...${NC}"
    subfinder -d "$target" -silent > "$output_dir/temp/subfinder.txt" 2>/dev/null
    echo -e "${GREEN}[+] subfinder completed: $(wc -l < "$output_dir/temp/subfinder.txt") subdomains found${NC}"
    
    # Run assetfinder
    echo -e "${YELLOW}[!] Running assetfinder...${NC}"
    assetfinder "$target" > "$output_dir/temp/assetfinder.txt" 2>/dev/null
    echo -e "${GREEN}[+] assetfinder completed: $(wc -l < "$output_dir/temp/assetfinder.txt") subdomains found${NC}"
    
    # Run findomain
    echo -e "${YELLOW}[!] Running findomain...${NC}"
    findomain -t "$target" --quiet > "$output_dir/temp/findomain.txt" 2>/dev/null
    echo -e "${GREEN}[+] findomain completed: $(wc -l < "$output_dir/temp/findomain.txt") subdomains found${NC}"
    
    # Run sublist3r
    echo -e "${YELLOW}[!] Running sublist3r...${NC}"
    sublist3r -d "$target" -o "$output_dir/temp/sublist3r.txt" >/dev/null 2>&1
    echo -e "${GREEN}[+] sublist3r completed: $(wc -l < "$output_dir/temp/sublist3r.txt") subdomains found${NC}"
    
    # Combine all results and remove duplicates
    echo -e "${YELLOW}[!] Combining results and removing duplicates...${NC}"
    cat "$output_dir/temp/"*.txt | sort -u > "$output_dir/all_subdomains.txt"
    
    # Count total unique subdomains
    local total_count=$(wc -l < "$output_dir/all_subdomains.txt")
    echo -e "${GREEN}[+] Total unique subdomains found: $total_count${NC}"
}

# Function to find alive subdomains
find_alive_subdomains() {
    local output_dir=$1
    
    echo -e "${YELLOW}[!] Probing for alive subdomains...${NC}"
    
    # Use httprobe to find alive domains
    cat "$output_dir/all_subdomains.txt" | httprobe -s -p https:443 | sed 's/https\?:\/\///' | tr -d ':443' | sort -u > "$output_dir/alive.txt"
    
    local alive_count=$(wc -l < "$output_dir/alive.txt")
    echo -e "${GREEN}[+] Alive subdomains found: $alive_count${NC}"
    
    # Create final target.txt file
    cp "$output_dir/alive.txt" "$output_dir/target.txt"
    echo -e "${GREEN}[+] Final results saved to: $output_dir/target.txt${NC}"
}

# Function to run waybackurls analysis
run_waybackurls() {
    local target=$1
    local output_dir=$2
    
    echo -e "${PURPLE}[*] Starting WaybackURLs analysis for: $target${NC}"
    
    # Create waybackurls directory
    local wayback_dir="$output_dir/waybackurls"
    mkdir -p "$wayback_dir"
    
    # Run waybackurls on the target domain
    echo -e "${CYAN}[!] Running waybackurls on target domain...${NC}"
    echo "$target" | waybackurls > "$wayback_dir/wayback_urls_raw.txt"
    echo -e "${GREEN}[+] waybackurls completed: $(wc -l < "$wayback_dir/wayback_urls_raw.txt") URLs found${NC}"
    
    # Run waybackurls on all subdomains if available
    if [ -f "$output_dir/all_subdomains.txt" ] && [ -s "$output_dir/all_subdomains.txt" ]; then
        echo -e "${CYAN}[!] Running waybackurls on all subdomains...${NC}"
        cat "$output_dir/all_subdomains.txt" | waybackurls > "$wayback_dir/wayback_subdomains_raw.txt"
        echo -e "${GREEN}[+] waybackurls on subdomains completed: $(wc -l < "$wayback_dir/wayback_subdomains_raw.txt") URLs found${NC}"
        
        # Combine all wayback URLs
        cat "$wayback_dir/wayback_urls_raw.txt" "$wayback_dir/wayback_subdomains_raw.txt" | sort -u > "$wayback_dir/all_wayback_urls.txt"
    else
        cp "$wayback_dir/wayback_urls_raw.txt" "$wayback_dir/all_wayback_urls.txt"
    fi
    
    local total_wayback=$(wc -l < "$wayback_dir/all_wayback_urls.txt")
    echo -e "${GREEN}[+] Total unique wayback URLs found: $total_wayback${NC}"
    
    # Extract domains from wayback URLs
    echo -e "${CYAN}[!] Extracting domains from wayback URLs...${NC}"
    cat "$wayback_dir/all_wayback_urls.txt" | sed -E 's|https?://([^/]+).*|\1|i' | sort -u > "$wayback_dir/wayback_domains.txt"
    echo -e "${GREEN}[+] Domains extracted: $(wc -l < "$wayback_dir/wayback_domains.txt")${NC}"
    
    # Find alive wayback domains
    echo -e "${CYAN}[!] Probing for alive wayback domains...${NC}"
    cat "$wayback_dir/wayback_domains.txt" | httprobe -s -p https:443 | sed 's/https\?:\/\///' | tr -d ':443' | sort -u > "$wayback_dir/wayback_alive.txt"
    
    local alive_wayback=$(wc -l < "$wayback_dir/wayback_alive.txt")
    echo -e "${GREEN}[+] Alive wayback domains found: $alive_wayback${NC}"
    
    # Find unique wayback domains that weren't in original subdomain list
    if [ -f "$output_dir/all_subdomains.txt" ]; then
        comm -13 <(sort "$output_dir/all_subdomains.txt") <(sort "$wayback_dir/wayback_alive.txt") > "$wayback_dir/wayback_unique_domains.txt"
        local unique_count=$(wc -l < "$wayback_dir/wayback_unique_domains.txt")
        echo -e "${GREEN}[+] Unique wayback domains (not in original list): $unique_count${NC}"
    fi
}

# Function to display results summary
show_summary() {
    local output_dir=$1
    local target=$2
    
    echo -e "${BLUE}"
    echo "=========================================="
    echo "           SCAN SUMMARY"
    echo "=========================================="
    echo -e "${NC}"
    echo -e "Target: ${GREEN}$target${NC}"
    echo -e "Output Directory: ${GREEN}$output_dir${NC}"
    echo -e "Total Subdomains Found: ${GREEN}$(wc -l < "$output_dir/all_subdomains.txt")${NC}"
    echo -e "Alive Subdomains: ${GREEN}$(wc -l < "$output_dir/alive.txt")${NC}"
    
    # WaybackURLs summary
    local wayback_dir="$output_dir/waybackurls"
    if [ -d "$wayback_dir" ]; then
        echo -e "WaybackURLs Total: ${PURPLE}$(wc -l < "$wayback_dir/all_wayback_urls.txt")${NC}"
        echo -e "WaybackURLs Alive: ${PURPLE}$(wc -l < "$wayback_dir/wayback_alive.txt")${NC}"
        if [ -f "$wayback_dir/wayback_unique_domains.txt" ]; then
            echo -e "WaybackURLs Unique: ${PURPLE}$(wc -l < "$wayback_dir/wayback_unique_domains.txt")${NC}"
        fi
    fi
    
    echo ""
    echo -e "${YELLOW}Files created:${NC}"
    echo -e "  - ${GREEN}$output_dir/all_subdomains.txt${NC} (All unique subdomains)"
    echo -e "  - ${GREEN}$output_dir/alive.txt${NC} (Alive subdomains)"
    echo -e "  - ${GREEN}$output_dir/target.txt${NC} (Final results)"
    
    # WaybackURLs files
    if [ -d "$wayback_dir" ]; then
        echo -e "${PURPLE}WaybackURLs files:${NC}"
        echo -e "  - ${PURPLE}$wayback_dir/all_wayback_urls.txt${NC} (All wayback URLs)"
        echo -e "  - ${PURPLE}$wayback_dir/wayback_domains.txt${NC} (Extracted domains)"
        echo -e "  - ${PURPLE}$wayback_dir/wayback_alive.txt${NC} (Alive wayback domains)"
        if [ -f "$wayback_dir/wayback_unique_domains.txt" ]; then
            echo -e "  - ${PURPLE}$wayback_dir/wayback_unique_domains.txt${NC} (Unique domains)"
        fi
    fi
    
    echo ""
    
    # Show first 10 alive subdomains as preview
    if [ -s "$output_dir/alive.txt" ]; then
        echo -e "${YELLOW}First 10 alive subdomains:${NC}"
        head -n 10 "$output_dir/alive.txt"
    fi
    
    # Show first 5 unique wayback domains if available
    if [ -f "$wayback_dir/wayback_unique_domains.txt" ] && [ -s "$wayback_dir/wayback_unique_domains.txt" ]; then
        echo ""
        echo -e "${PURPLE}First 5 unique wayback domains:${NC}"
        head -n 5 "$wayback_dir/wayback_unique_domains.txt"
    fi
}

# Main function
main() {
    # Check if target is provided
    if [ $# -eq 0 ]; then
        echo -e "${RED}[-] Usage: $0 <target-domain>${NC}"
        echo -e "${YELLOW}Example: $0 example.com${NC}"
        exit 1
    fi
    
    local target=$1
    local output_dir="$PWD/$target"
    
    # Create output directory
    mkdir -p "$output_dir"
    
    # Install dependencies
    install_dependencies
    
    # Run enumeration
    run_enumeration "$target" "$output_dir"
    
    # Find alive subdomains
    find_alive_subdomains "$output_dir"
    
    # Run waybackurls analysis
    run_waybackurls "$target" "$output_dir"
    
    # Show summary
    show_summary "$output_dir" "$target"
    
    # Cleanup temporary files
    rm -rf "$output_dir/temp"
    
    echo -e "${GREEN}"
    echo "=========================================="
    echo "           SCAN COMPLETED!"
    echo "=========================================="
    echo -e "${NC}"
}

# Run main function with all arguments
main "$@"
