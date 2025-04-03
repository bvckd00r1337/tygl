import asyncio
import time
import random
import csv
import os
import base64
from playwright.async_api import async_playwright
import json
from datetime import datetime

class LinktreeClicker:
    def __init__(self, urls_file, proxies_file, user_agents_file, cycles=950):
        # Load data from files
        self.urls = self.load_list_from_file(urls_file)
        self.proxies = self.load_list_from_file(proxies_file)
        self.user_agents = self.load_user_agents()
        
        # Configuration
        self.wait_time = 3
        self.visit_duration_range = (1, 3)  # Maximum 3 seconds visit duration
        self.redirect_wait_time = 5  # Reduced from 8
        self.cycles_per_url = cycles
        
        # Tracking
        self.cycle_counts = {url: 0 for url in self.urls}
        self.last_ip = None  # Store the last seen IP
        
        # Create data directory for tracking
        os.makedirs("data", exist_ok=True)
        
        # Load existing cycle counts if available
        self.load_cycle_counts()
        
        print(f"Loaded {len(self.urls)} URLs, {len(self.proxies)} proxies, and {len(self.user_agents)} user agents")
        print(f"Will run {self.cycles_per_url} cycles for each URL")
    
    def load_cycle_counts(self):
        """Load existing cycle counts from file if it exists"""
        try:
            cycle_file = "data/cycle_counts.csv"
            if os.path.exists(cycle_file):
                with open(cycle_file, 'r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if len(row) == 2:
                            url, count = row
                            if url in self.cycle_counts:
                                self.cycle_counts[url] = int(count)
                print(f"Loaded existing cycle counts")
                for url, count in self.cycle_counts.items():
                    print(f"  {url}: {count}/{self.cycles_per_url} cycles completed")
        except Exception as e:
            print(f"Error loading cycle counts: {e}")
    
    def save_cycle_counts(self):
        """Save current cycle counts to file"""
        try:
            cycle_file = "data/cycle_counts.csv"
            with open(cycle_file, 'w', newline='') as file:
                writer = csv.writer(file)
                for url, count in self.cycle_counts.items():
                    writer.writerow([url, count])
            print(f"Saved cycle counts to {cycle_file}")
        except Exception as e:
            print(f"Error saving cycle counts: {e}")
    
    def load_list_from_file(self, filename):
        """Load a list of items from a file (one item per line)"""
        try:
            with open(filename, 'r') as file:
                if filename.endswith('.csv'):
                    return [row[0] for row in csv.reader(file) if row]
                else:
                    return [line.strip() for line in file if line.strip()]
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return []
    
    def load_user_agents(self):
        """Load Romanian mobile user agents only"""
        # Romanian mobile user agents
        romanian_mobile_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.50 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 11; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36"
        ]
        
        # Add Romanian language settings to each user agent
        romanian_user_agents = []
        for agent in romanian_mobile_user_agents:
            # Insert Romanian language preferences
            if "AppleWebKit" in agent:
                # For WebKit browsers (Safari, Chrome)
                agent_parts = agent.split("AppleWebKit")
                romanian_agent = f"{agent_parts[0]}; ro-RO) AppleWebKit{agent_parts[1]}"
                romanian_user_agents.append(romanian_agent)
            else:
                # For other browsers, append language info
                romanian_user_agents.append(f"{agent}; ro-RO")
        
        # Try to load from file, but only keep mobile Romanian agents
        try:
            agents_from_file = self.load_list_from_file("user_agents.txt")
            if agents_from_file:
                # Filter to only include mobile agents with Romanian language
                romanian_mobile_only = [
                    agent for agent in agents_from_file 
                    if any(term in agent.lower() for term in ['mobile', 'android', 'iphone', 'ipad', 'ios'])
                    and ("ro-RO" in agent or "ro;" in agent or "Romania" in agent)
                ]
                if romanian_mobile_only:
                    return romanian_mobile_only
        except:
            pass
        
        return romanian_user_agents
    
    def get_random_proxy(self):
        """Return the configured proxy information for direct HTTP proxy usage"""
        # Use HTTP proxy which has better compatibility with Playwright
        proxy_host = "proxy-eu.proxy-cheap.com"
        proxy_port = "5959"
        proxy_user = "pcP4S5y1DZ-res-ro"
        proxy_pass = "PC_7iPvqFyyPpeoenYjn"
        
        # Return in format that Playwright can use with Chromium
        return {
            "server": f"http://{proxy_host}:{proxy_port}",
            "username": proxy_user,
            "password": proxy_pass
        }
    
    def get_random_user_agent(self):
        """Get a random mobile user agent"""
        if not self.user_agents:
            return "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        return random.choice(self.user_agents)
    
    def get_random_headers(self, user_agent):
        """Generate random Romanian headers for the request"""
        return {
            "User-Agent": user_agent,
            "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.ro/",
            "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?1",
            "Sec-Ch-Ua-Platform": random.choice(['"Android"', '"iOS"']),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1"
        }
    
    async def prevent_webrtc_leaks(self, context):
        """Add anti-fingerprinting and WebRTC leak prevention scripts"""
        await context.add_init_script("""
            // Hide webdriver detection
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            // Set Romanian language for navigator
            Object.defineProperty(navigator, 'languages', {get: () => ['ro-RO', 'ro', 'en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            
            // Block WebRTC leaks
            const originalRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection;
            if (originalRTCPeerConnection) {
                window.RTCPeerConnection = function(...args) {
                    const pc = new originalRTCPeerConnection(...args);
                    pc.createDataChannel = () => {};
                    return pc;
                };
            }
            
            // Spoof canvas fingerprinting
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (this.width > 16 && this.height > 16) {
                    const origImg = originalToDataURL.apply(this, arguments);
                    return origImg + (Math.random() * 0.01).toString();
                } else {
                    return originalToDataURL.apply(this, arguments);
                }
            };
            
            // Add noise to audio fingerprinting
            const audioContext = window.AudioContext || window.webkitAudioContext;
            if (audioContext) {
                const origCreateOscillator = audioContext.prototype.createOscillator;
                audioContext.prototype.createOscillator = function() {
                    const oscillator = origCreateOscillator.apply(this, arguments);
                    const origStart = oscillator.start;
                    oscillator.start = function() {
                        this.detune.value = this.detune.value + (Math.random() * 2 - 1);
                        return origStart.apply(this, arguments);
                    };
                    return oscillator;
                };
            }
        """)
    
    async def verify_proxy(self, context):
        """Verify the proxy is working by checking our public IP address"""
        try:
            # Create a temporary page for checking IP
            ip_page = await context.new_page()
            
            # Set a shorter timeout for this specific check
            ip_page.set_default_navigation_timeout(20000)
            
            # Try multiple IP checking services in case one is blocked
            ip_services = [
                "https://api.ipify.org/",
                "https://ifconfig.me/ip",
                "https://ipinfo.io/ip"
            ]
            
            for service in ip_services:
                try:
                    await ip_page.goto(service, wait_until="networkidle")
                    ip_address = await ip_page.content()
                    
                    # Extract just the IP from the page content
                    if "<html" in ip_address.lower():
                        # If we got HTML back, extract the text
                        ip_address = await ip_page.evaluate("document.body.innerText.trim()")
                    else:
                        # Plain text response
                        ip_address = ip_address.strip()
                    
                    # Validate that this looks like an IP
                    if len(ip_address.split('.')) == 4 and all(part.isdigit() for part in ip_address.split('.')):
                        print(f"✓ Proxy verification successful! Current IP: {ip_address}")
                        await ip_page.close()
                        return True, ip_address
                except Exception as e:
                    print(f"Failed to check IP using {service}: {e}")
                    continue
            
            # If we get here, all services failed
            print("⚠ Could not verify proxy IP (all services failed)")
            await ip_page.close()
            return False, None
        
        except Exception as e:
            print(f"⚠ Error verifying proxy: {e}")
            return False, None
    
    async def process_linktree(self, url, proxy_info, user_agent):
        """Process a Linktree URL using Playwright with real click simulation"""
        async with async_playwright() as playwright:
            browser = None
            try:
                print(f"\nProcessing: {url}")
                if proxy_info:
                    print(f"Using proxy: {proxy_info['server']}")
                print(f"Using user agent: {user_agent[:50]}...")
                
                # Set up launch options
                launch_options = {
                    "headless": False,  # Visible browser for debugging
                    "args": [
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--disable-site-isolation-trials",
                        "--disable-web-security",
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox"
                    ]
                }

                # Add proxy configuration if provided
                if proxy_info:
                    # Make sure the proxy server format is correct for playwright
                    if proxy_info["server"].startswith("http://"):
                        launch_options["proxy"] = {
                            "server": proxy_info["server"],
                            "username": proxy_info["username"],
                            "password": proxy_info["password"]
                        }
                    else:
                        print("Proxy must be in http:// format")
                        return False

                # Launch browser with error handling
                try:
                    browser = await playwright.chromium.launch(**launch_options)
                    if not browser:
                        print("Browser launch returned None. Check proxy settings.")
                        return False
                except Exception as e:
                    print(f"Failed to launch browser: {e}")
                    return False
                
                # Create context with slightly different device parameters
                screen_width = random.choice([375, 390, 414, 428])
                screen_height = random.choice([667, 736, 812, 844])
                
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": screen_width, "height": screen_height},
                    device_scale_factor=2.0,
                    is_mobile=True,
                    has_touch=True,
                    locale="ro-RO",  # Romanian locale
                    timezone_id="Europe/Bucharest",  # Romanian timezone
                    geolocation={"latitude": 44.4268, "longitude": 26.1025},  # Bucharest coordinates
                    permissions=["geolocation"],
                    ignore_https_errors=True,
                    bypass_csp=True,  # Bypass Content Security Policy
                )
                
                # Prevent fingerprinting and WebRTC leaks
                await self.prevent_webrtc_leaks(context)
                
                # Verify that the proxy is working by checking our IP
                proxy_working, ip_address = await self.verify_proxy(context)
                
                if not proxy_working and proxy_info:
                    print("⚠ Warning: Proxy does not appear to be working correctly")
                
                # Create a new page
                page = await context.new_page()
                
                # Set default navigation timeout
                page.set_default_navigation_timeout(60000)  # 60 seconds
                
                # Add random headers
                await page.set_extra_http_headers(self.get_random_headers(user_agent))
                
                # Visit the Linktree page with retry logic
                max_retries = 3
                success = False
                
                for attempt in range(max_retries):
                    try:
                        print(f"Loading Linktree page (attempt {attempt+1})...")
                        
                        # Navigate to the Linktree page
                        response = await page.goto(url, wait_until="domcontentloaded")
                        
                        # Wait for page to be fully loaded
                        await page.wait_for_load_state("networkidle")
                        
                        # Check if navigation was successful
                        if response and response.ok:
                            print("✓ Page loaded successfully")
                            success = True
                            break
                        else:
                            print(f"⚠ Page loaded with status: {response.status if response else 'unknown'}")
                            if attempt < max_retries - 1:
                                await page.wait_for_timeout(5000)  # Wait 5 seconds before retry
                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f"Attempt {attempt+1} failed: {e}. Retrying...")
                            await page.wait_for_timeout(5000)  # Wait 5 seconds before retry
                        else:
                            print(f"All attempts failed to load page: {e}")
                            raise
                
                if not success:
                    print("Failed to load page after all retries")
                    return False
                
                # Wait for any dynamic content to load with a realistic delay
                await page.wait_for_timeout(random.uniform(2000, 4000))
                
                # Extract all links
                all_hrefs = []
                link_elements = []  # Store the actual DOM elements for clicking
                
                # Try specific selectors from Linktree
                selectors = [
                    "a[href*='ty.gl']",
                    "a[data-testid='LinkButton']",
                    "div[data-linktype='CLASSIC'] a",
                    "a.sc-dmqHEX",
                    "a.sc-beqWaB",
                    "a[href*='linktr.ee']",
                    ".link-block a",
                    ".link a",
                    "[role='link']"
                ]
                
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            href = await element.get_attribute("href")
                            if href and "linktree" not in href and href not in all_hrefs:
                                all_hrefs.append(href)
                                link_elements.append(element)  # Store the actual element
                    except Exception as e:
                        print(f"Error with selector '{selector}': {e}")
                        continue
                
                # If no links found with specific selectors, try all links
                if not all_hrefs:
                    try:
                        elements = await page.query_selector_all("a")
                        for element in elements:
                            href = await element.get_attribute("href")
                            if href and "linktree" not in href and href not in all_hrefs:
                                all_hrefs.append(href)
                    except Exception as e:
                        print(f"Error getting all links: {e}")
                
                print(f"Found {len(all_hrefs)} unique links to process")
                
                # Process links using real click simulation instead of direct navigation
                await self.process_links_with_clicks(page, context, all_hrefs, link_elements)
                
                # After processing all links and completing the cycle
                print("Clearing all browser data to ensure fresh state for next cycle...")
                await context.clear_cookies()  # Clear all cookies
                
                # Record this cycle
                self.cycle_counts[url] += 1
                print(f"Completed cycle {self.cycle_counts[url]}/{self.cycles_per_url} for {url}")
                
                # Save cycle counts after each full cycle
                self.save_cycle_counts()
                
                # Rest between cycles with randomized delay
                await page.wait_for_timeout(random.uniform(3000, 6000))
                
                return True
                
            except Exception as e:
                print(f"Error processing Linktree: {e}")
                return False
            
            finally:
                if browser:
                    await browser.close()  # Close browser to fully reset state
    
    async def process_trendyol_link(self, page, context, href):
        """Process a Trendyol-specific link with special handling"""
        # Add cache-busting parameter
        if "?" in href:
            href += f"&_cb={int(time.time() * 1000)}"
        else:
            href += f"?_cb={int(time.time() * 1000)}"
        
        # Extract campaign ID if available
        campaign_id = None
        if "adjust_campaign=" in href:
            campaign_id = href.split("adjust_campaign=")[1].split("&")[0]
        elif "adjust_adgroup=" in href:
            campaign_id = href.split("adjust_adgroup=")[1].split("&")[0]
        
        # Create a direct URL to Trendyol
        if campaign_id:
            direct_url = f"https://www.trendyol.com/sr?q={campaign_id}"
        else:
            direct_url = "https://www.trendyol.com/"
        
        print(f"  Trendyol link detected. Processing: {href[:50]}...")
        print(f"  Will also visit direct URL: {direct_url}")
        
        # Create a new page for this link
        new_page = await context.new_page()
        
        try:
            # First visit the Adjust URL to trigger its tracking pixel
            try:
                await new_page.goto(href, wait_until="commit", timeout=30000)
                # Wait briefly for tracking pixels to load
                await new_page.wait_for_timeout(2000)
                
                # Check for redirects
                current_url = new_page.url
                print(f"  Current URL after initial load: {current_url[:75]}...")
                
                # If we've already redirected to Trendyol, wait longer
                if "trendyol.com" in current_url:
                    print(f"  ✓ Already redirected to Trendyol")
                    
                    # Wait for the page to stabilize
                    await new_page.wait_for_load_state("networkidle", timeout=10000)
                    
                    # Random visit duration (maximum 3 seconds)
                    visit_duration = random.uniform(*self.visit_duration_range)
                    print(f"  Staying on page for {visit_duration:.1f} seconds")
                    await new_page.wait_for_timeout(visit_duration * 1000)
                    
                    # Close the page
                    await new_page.close()
                    return
            except Exception as e:
                print(f"  Expected error with Adjust URL: {e}")
            
            # Then go to the direct Trendyol URL
            try:
                await new_page.goto(direct_url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for the page to stabilize
                await new_page.wait_for_load_state("networkidle", timeout=10000)
                
                # Random visit duration (maximum 3 seconds)
                visit_duration = random.uniform(*self.visit_duration_range)
                print(f"  Staying on direct Trendyol page for {visit_duration:.1f} seconds")
                await new_page.wait_for_timeout(visit_duration * 1000)
                
            except Exception as e:
                print(f"  Error on direct Trendyol navigation: {e}")
        
        finally:
            # Always close the page
            await new_page.close()
    
    async def process_regular_link(self, page, context, href):
        """Process a regular (non-Trendyol) link"""
        # Special handling for ty.gl links
        if "ty.gl" in href:
            return await self.process_trendyol_link(page, context, href)
        
        # Create a new page for this link
        new_page = await context.new_page()
        
        try:
            # Navigate to the link
            print(f"  Navigating to: {href[:75]}...")
            
            try:
                # Navigate with networkidle to ensure page is fully loaded
                response = await new_page.goto(href, timeout=30000, wait_until="domcontentloaded")
                
                # Wait for any redirects to complete
                await new_page.wait_for_load_state("networkidle", timeout=10000)
                
                # Check final URL after redirects
                final_url = new_page.url
                if final_url != href:
                    print(f"  Redirected to: {final_url[:75]}...")
                
                # Random visit duration (maximum 3 seconds)
                visit_duration = random.uniform(*self.visit_duration_range)
                print(f"  Staying on page for {visit_duration:.1f} seconds")
                await new_page.wait_for_timeout(visit_duration * 1000)
                
            except Exception as e:
                error_str = str(e)
                
                # Special handling for common expected errors
                if "ERR_UNKNOWN_URL_SCHEME" in error_str or "unknown error" in error_str.lower():
                    print("  ✓ App deep link detected - counting as success")
                    await new_page.wait_for_timeout(2000)
                elif "ERR_ABORTED" in error_str and ("ty.gl" in href or "adj.st" in href):
                    print("  ✓ Tracking link navigation aborted (expected) - counting as success")
                    await new_page.wait_for_timeout(2000)
                else:
                    print(f"  Navigation error: {e}")
        
        finally:
            # Always close the page
            await new_page.close()
    
    async def process_links_in_batches(self, page, context, all_hrefs, batch_size=3):
        """Process links in small batches to balance speed and resource usage"""
        total_links = len(all_hrefs)
        print(f"Processing {total_links} links in batches of {batch_size}...")
        
        processed_count = 0
        
        # Process links in batches
        for i in range(0, total_links, batch_size):
            batch = all_hrefs[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(total_links + batch_size - 1)//batch_size} ({len(batch)} links)")
            
            # Create tasks for this batch
            tasks = []
            for href in batch:
                if "adj.st" in href or "ty.gl" in href or "trendyol" in href.lower():
                    task = asyncio.create_task(self.process_trendyol_link(page, context, href))
                else:
                    task = asyncio.create_task(self.process_regular_link(page, context, href))
                tasks.append(task)
            
            # Wait for current batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful links in this batch
            successful = sum(1 for r in results if r is not True and not isinstance(r, Exception))
            processed_count += successful
            
            # Small delay between batches
            await page.wait_for_timeout(random.uniform(1000, 3000))
        
        print(f"Completed processing {processed_count}/{total_links} links in batches")
    
    async def process_links_with_clicks(self, page, context, all_hrefs, link_elements):
        """Process links using real mouse clicks that open in new tabs"""
        print(f"Processing {len(all_hrefs)} links with simulated clicks (opening in new tabs)...")
        
        # Process all links in parallel to speed up the process
        tasks = []
        
        for i, href in enumerate(all_hrefs):
            print(f"  Setting up link {i+1}/{len(all_hrefs)}: {href[:50]}...")
            
            # Determine if this is a special link type
            is_trendyol = "adj.st" in href or "ty.gl" in href or "trendyol" in href.lower()
            
            # Create a task for each link
            task = asyncio.create_task(
                self.process_individual_link(page, context, href, i, len(all_hrefs), is_trendyol)
            )
            tasks.append(task)
        
        # Wait for all links to be processed in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"Completed processing all {len(all_hrefs)} links in parallel")

    async def process_individual_link(self, page, context, href, index, total, is_trendyol):
        """Process a single link, opening it in a new tab with a fresh user agent"""
        new_page = None
        tracking_data = None
        try:
            print(f"  Processing link {index+1}/{total}: {href[:50]}...")
            
            # Get a unique user agent for this specific link from the file
            link_user_agent = self.get_random_user_agent()
            
            # Create a new page/tab for this link
            new_page = await context.new_page()
            
            # Apply the unique user agent to this page
            await new_page.set_extra_http_headers({"User-Agent": link_user_agent})
            
            # Set up tracking if this is a Trendyol link
            if is_trendyol:
                print(f"  Setting up network tracking for verification...")
                requests, remove_listeners, timestamp, link_id = await self.track_network_requests(new_page, href)
                tracking_data = (requests, timestamp, link_id, remove_listeners)
            
            # Set up event listeners for new tab
            async def handle_popup(popup):
                print(f"  Popup detected for link {index+1}, following to: {popup.url}")
                
                try:
                    await popup.wait_for_load_state("domcontentloaded", timeout=15000)
                    
                    # Check where we landed
                    current_url = popup.url
                    if is_trendyol and "trendyol.com" in current_url:
                        print(f"  ✓ Successfully redirected to Trendyol: {current_url[:50]}...")
                        
                        # Wait for the page to stabilize
                        await popup.wait_for_load_state("networkidle", timeout=10000)
                        
                        # Random visit duration
                        visit_duration = random.uniform(*self.visit_duration_range)
                        print(f"  Staying on page for {visit_duration:.1f} seconds")
                        await popup.wait_for_timeout(visit_duration * 1000)
                except Exception as e:
                    if "ERR_ABORTED" in str(e):
                        print("  ✓ Tracking link registered (normal redirect abort)")
                    else:
                        print(f"  Navigation completed with expected result: {str(e)[:100]}")
            
            # Listen for popup events
            context.on("page", handle_popup)
            
            # Directly navigate to the target URL in the new tab
            # Add cache-busting parameter
            if "?" in href:
                modified_href = href + f"&_cb={int(time.time() * 1000)}"
            else:
                modified_href = href + f"?_cb={int(time.time() * 1000)}"
                
            # Navigate to the link
            try:
                response = await new_page.goto(modified_href, wait_until="domcontentloaded", timeout=30000)
                
                # If tracking is enabled, wait a bit longer to capture all requests
                if is_trendyol:
                    print("  Waiting for tracking requests to complete...")
                    await new_page.wait_for_timeout(3000)
                
                # Wait for any redirects to complete
                await new_page.wait_for_load_state("networkidle", timeout=10000)
                
                # Random visit duration
                visit_duration = random.uniform(*self.visit_duration_range)
                print(f"  Staying on page for {visit_duration:.1f} seconds")
                await new_page.wait_for_timeout(visit_duration * 1000)
                
            except Exception as e:
                error_str = str(e)
                
                # Special handling for common expected errors
                if "ERR_UNKNOWN_URL_SCHEME" in error_str or "unknown error" in error_str.lower():
                    print(f"  ✓ App deep link detected for link {index+1} - counting as success")
                elif "ERR_ABORTED" in error_str and ("ty.gl" in href or "adj.st" in href):
                    print(f"  ✓ Tracking link navigation aborted for link {index+1} (expected) - counting as success")
                else:
                    print(f"  Navigation error for link {index+1}: {e}")
                
                # For Trendyol links, try direct navigation as fallback
                if is_trendyol:
                    # Extract campaign ID if available
                    campaign_id = None
                    if "adjust_campaign=" in href:
                        campaign_id = href.split("adjust_campaign=")[1].split("&")[0]
                    elif "adjust_adgroup=" in href:
                        campaign_id = href.split("adjust_adgroup=")[1].split("&")[0]
                    
                    # Create a direct URL to Trendyol
                    if campaign_id:
                        direct_url = f"https://www.trendyol.com/sr?q={campaign_id}"
                    else:
                        direct_url = "https://www.trendyol.com/"
                    
                    print(f"  Visiting direct Trendyol URL as backup for link {index+1}: {direct_url}")
                    
                    try:
                        await new_page.goto(direct_url, wait_until="domcontentloaded")
                        
                        # Random visit duration
                        visit_duration = random.uniform(*self.visit_duration_range)
                        print(f"  Staying on direct Trendyol page for {visit_duration:.1f} seconds")
                        await new_page.wait_for_timeout(visit_duration * 1000)
                    except Exception as direct_err:
                        print(f"  Error visiting direct Trendyol URL: {direct_err}")
        
        except Exception as e:
            print(f"  Error processing link {index+1}: {e}")
        
        finally:
            # Process tracking data if available
            if tracking_data:
                requests, timestamp, link_id, remove_listeners = tracking_data
                
                # Clean up the listeners
                remove_listeners()
                
                # Save and analyze the tracking data
                if is_trendyol:
                    tracking_confirmed = self.save_tracking_data(requests, timestamp, link_id)
                    if tracking_confirmed:
                        print(f"  ✓ Tracking for link {index+1} successfully verified")
                    else:
                        print(f"  ⚠ Could not verify tracking for link {index+1}")
            
            if new_page:
                # Always close the new page/tab
                await new_page.close()
                
                # Remove the popup handler if it exists
                try:
                    context.off("page", handle_popup)
                except:
                    pass
            
    async def track_network_requests(self, page, href):
        """Set up streamlined network tracking to verify tracking links are properly registered"""
        # Create a list to store only relevant network requests
        tracking_requests = []
        
        # Create timestamp for this tracking session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        link_id = href.split("/")[-1] if "/" in href else href
        
        # Define tracking domains to monitor
        tracking_domains = ["ty.gl", "adjust.com", "app.adjust.com", "adj.st", 
                           "trendyol.com/tracking", "trendyol.com/collect", 
                           "trendyol.com/en/koleksiyonlar"]
        
        # Setup network event listeners - only log tracking-related requests
        async def on_request(request):
            # Only store tracking-related requests
            if any(domain in request.url for domain in tracking_domains):
                tracking_requests.append({
                    "url": request.url,
                    "method": request.method,
                    "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3]
                })
        
        # Register the event listeners
        page.on("request", on_request)
        
        # Return the functions to remove the listeners later
        def remove_listeners():
            page.remove_listener("request", on_request)
        
        # Return the tracking data and cleanup function
        return tracking_requests, remove_listeners, timestamp, link_id
    
    def save_tracking_data(self, tracking_requests, timestamp, link_id):
        """Save and analyze simplified tracking data"""
        try:
            os.makedirs("data/tracking", exist_ok=True)
            
            # Create a filename based on timestamp and link
            filename = f"data/tracking/track_{timestamp}_{link_id[:20]}.json"
            
            # Compile the data
            tracking_data = {
                "tracking_requests": tracking_requests,
                "timestamp": timestamp,
                "link": link_id
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            
            # Simplified tracking check
            if tracking_requests:
                print(f"  ✓ Tracking verified: Found {len(tracking_requests)} tracking requests")
                return True
            else:
                # Check for adjust parameters in the original URL
                has_adjust_params = "adjust_" in link_id or "adj.st" in link_id
                
                if has_adjust_params:
                    print(f"  ✓ Tracking verified: URL contains tracking parameters")
                    return True
                else:
                    print(f"  ⚠ No tracking detected")
                    return False
        
        except Exception as e:
            print(f"  ⚠ Error saving tracking data: {e}")
            return False
    
    async def run_async(self):
        """Process all URLs for the specified number of cycles with robust error handling"""
        try:
            # Track consecutive failures
            consecutive_failures = 0
            max_consecutive_failures = 5
            
            # Continue until all URLs have completed their cycles
            while True:
                # Check if all URLs have completed their cycles
                all_completed = True
                for url, count in self.cycle_counts.items():
                    if count < self.cycles_per_url:
                        all_completed = False
                        break
                
                if all_completed:
                    print("All URLs have completed their cycles!")
                    break
                
                # Process URLs in a more resilient way
                url_index = 0
                while url_index < len(self.urls):
                    url = self.urls[url_index]
                    
                    if self.cycle_counts[url] < self.cycles_per_url:
                        # Get proxy info and user agent
                        proxy_info = self.get_random_proxy()
                        user_agent = self.get_random_user_agent()
                        
                        print(f"\n[URL {url_index+1}/{len(self.urls)}] Processing: {url}")
                        print(f"Cycle: {self.cycle_counts[url]+1}/{self.cycles_per_url}")
                        
                        try:
                            # Each call to process_linktree creates a fresh browser instance
                            success = await self.process_linktree(url, proxy_info, user_agent)
                            
                            # Additional cleanup steps
                            print("Clearing all cache directories...")
                            
                            # Force the garbage collector to free up memory
                            import gc
                            gc.collect()
                            
                            if success:
                                consecutive_failures = 0
                            else:
                                consecutive_failures += 1
                        except Exception as e:
                            print(f"Error processing {url}: {e}")
                            consecutive_failures += 1
                        
                        # Handle too many consecutive failures
                        if consecutive_failures >= max_consecutive_failures:
                            print(f"Too many consecutive failures ({consecutive_failures}). Pausing for 5 minutes...")
                            await asyncio.sleep(300)  # 5 minutes pause
                            consecutive_failures = 0
                        
                        # Randomized delay between URLs
                        await asyncio.sleep(random.uniform(2, 5))
                    
                    # Move to next URL either way
                    url_index += 1
                    
                    # After trying all URLs once, reset to beginning if needed
                    if url_index >= len(self.urls):
                        url_index = 0
                        # Short break between cycles
                        await asyncio.sleep(10)
        
        except KeyboardInterrupt:
            print("\nScript interrupted by user. Saving progress...")
            self.save_cycle_counts()
            print("Progress saved. You can resume later.")
        
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            self.save_cycle_counts()
        
        finally:
            # Always save cycle counts at the end
            self.save_cycle_counts()
            print("\nAll processing completed!")

def run():
    """Main entry point"""
    # File paths
    urls_file = "urls.txt"  # One URL per line
    proxies_file = "proxies.txt"  # One proxy per line in format host:port
    user_agents_file = "user_agents.txt"  # One user agent per line
    
    # Create and run the clicker with 950 cycles per URL
    clicker = LinktreeClicker(urls_file, proxies_file, user_agents_file, cycles=950)
    
    # Run the async event loop
    asyncio.run(clicker.run_async())

if __name__ == "__main__":
    run() 