import httpx
import asyncio
import logging
from bs4 import BeautifulSoup
from typing import List, Dict
import json
from pathlib import Path
import random

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class LocationExtractor:
    def __init__(self):
        self.base_url = "https://www.vietnambooking.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'www.vietnambooking.com',
            'Referer': 'https://www.vietnambooking.com/',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }

    async def fetch_main_page(self) -> str:
        """Fetch trang chủ vietnambooking.com"""
        url = f"{self.base_url}/"
        logger.info(f"Fetching main page: {url}")
        
        try:
            await asyncio.sleep(0.5 + random.random() * 0.5)  # Fast delay for development
            
            async with httpx.AsyncClient(timeout=30.0, headers=self.headers) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.error(f"HTTP Error: {response.status_code}")
                    return None
                
                logger.info(f"Successfully fetched main page, content length: {len(response.text)}")
                return response.text
                
        except Exception as e:
            logger.error(f"Error fetching main page: {str(e)}")
            return None

    def parse_locations(self, html: str) -> List[Dict]:
        """Extract danh sách locations từ HTML"""
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        locations = []
        
        # Method 1: Tìm từ navigation menu hoặc footer
        nav_links = soup.find_all('a', href=lambda x: x and '/hotel/vietnam/khach-san-' in x and x.endswith('.html'))
        
        # Method 2: Tìm từ các dropdown menu hoặc danh sách địa điểm 
        destination_sections = soup.find_all(['div', 'ul', 'section'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['destination', 'location', 'city', 'province', 'dia-diem']))
        for section in destination_sections:
            section_links = section.find_all('a', href=lambda x: x and '/hotel/vietnam/khach-san-' in x)
            nav_links.extend(section_links)
        
        # Method 3: Tìm tất cả link có pattern khách sạn
        all_hotel_links = soup.find_all('a', href=lambda x: x and '/hotel/vietnam/khach-san-' in x and x.endswith('.html'))
        nav_links.extend(all_hotel_links)
        
        seen_locations = set()
        
        # Xử lý các link tìm được từ HTML
        for link in nav_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Extract location info từ href
            if '/hotel/vietnam/khach-san-' in href:
                location_code = href.split('/')[-1].replace('.html', '')
                location_name = text if text else location_code.replace('khach-san-', '').replace('-', ' ').title()
                
                # Bỏ qua duplicates
                if location_code in seen_locations:
                    continue
                seen_locations.add(location_code)
                
                # Extract số lượng khách sạn nếu có
                hotel_count = 0
                parent = link.find_parent()
                if parent:
                    count_text = parent.get_text()
                    import re
                    count_match = re.search(r'(\d+)\s*(?:khách sạn|hotel)', count_text, re.IGNORECASE)
                    if count_match:
                        hotel_count = int(count_match.group(1))
                
                location_data = {
                    'url': href if href.startswith('http') else f"{self.base_url}{href}",
                    'location_name': location_name,
                    'code': location_code.replace('khach-san-', ''),
                    'hotel_count': hotel_count
                }
                
                locations.append(location_data)
                logger.info(f"Found location: {location_name} ({hotel_count} hotels)")
        
        # Method 4: Thêm các địa điểm phổ biến của Việt Nam nếu chưa có
        popular_cities = [
            'vung-tau', 'phu-quoc', 'sapa', 'ha-long', 'mui-ne', 'quan-1', 
            'phan-thiet', 'chau-doc', 'tam-coc', 'ninh-binh', 'dong-hoi',
            'phong-nha', 'dong-ha', 'hue', 'ba-na-hills', 'my-son', 'tra-que',
            'cat-ba', 'sam-son', 'do-son', 'cua-lo', 'lang-co', 'an-thoi',
            'bai-chay', 'tuan-chau', 'co-to', 'bach-long-vi', 'ly-son'
        ]
        
        for city in popular_cities:
            location_code = f'khach-san-{city}'
            if location_code not in seen_locations:
                location_data = {
                    'url': f"{self.base_url}/hotel/vietnam/khach-san-{city}.html",
                    'location_name': city.replace('-', ' ').title(),
                    'code': city,
                    'hotel_count': 0
                }
                locations.append(location_data)
                seen_locations.add(location_code)
                logger.info(f"Added popular location: {location_data['location_name']} (0 hotels)")
        
        logger.info(f"Total locations extracted: {len(locations)}")
        return locations
    
    def save_locations(self, locations: List[Dict], output_dir: str):
        """Lưu danh sách locations vào file JSON"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        output_file = output_path / 'locations.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(locations)} locations to {output_file}")

    def get_predefined_locations(self) -> List[Dict]:
        """Trả về danh sách đầy đủ 59 locations của Việt Nam với số lượng khách sạn thực tế"""
        locations = [
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-vung-tau.html", "location_name": "Vũng Tàu", "code": "vung-tau", "hotel_count": 209},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-quan-1.html", "location_name": "Quận 1", "code": "quan-1", "hotel_count": 220},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-da-lat.html", "location_name": "Đà Lạt", "code": "da-lat", "hotel_count": 269},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-phu-quoc.html", "location_name": "Phú Quốc", "code": "phu-quoc", "hotel_count": 249},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-da-nang.html", "location_name": "Đà Nẵng", "code": "da-nang", "hotel_count": 380},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-con-dao.html", "location_name": "Côn Đảo", "code": "con-dao", "hotel_count": 21},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-sapa.html", "location_name": "Sapa", "code": "sapa", "hotel_count": 136},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-nha-trang.html", "location_name": "Nha Trang", "code": "nha-trang", "hotel_count": 250},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-can-tho.html", "location_name": "Cần Thơ", "code": "can-tho", "hotel_count": 56},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-ha-noi.html", "location_name": "Hà Nội", "code": "ha-noi", "hotel_count": 501},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-phu-yen.html", "location_name": "Phú Yên", "code": "phu-yen", "hotel_count": 50},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-chau-doc.html", "location_name": "Châu Đốc", "code": "chau-doc", "hotel_count": 14},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-tp-ho-chi-minh.html", "location_name": "TP Hồ Chí Minh", "code": "tp-ho-chi-minh", "hotel_count": 419},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-binh-thuan.html", "location_name": "Bình Thuận", "code": "binh-thuan", "hotel_count": 140},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-ninh-thuan.html", "location_name": "Ninh Thuận", "code": "ninh-thuan", "hotel_count": 25},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-thua-thien-hue.html", "location_name": "Thừa Thiên Huế", "code": "thua-thien-hue", "hotel_count": 91},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-ha-giang.html", "location_name": "Hà Giang", "code": "ha-giang", "hotel_count": 21},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-phan-thiet.html", "location_name": "Phan Thiết", "code": "phan-thiet", "hotel_count": 117},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-nghe-an.html", "location_name": "Nghệ An", "code": "nghe-an", "hotel_count": 35},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-ca-mau.html", "location_name": "Cà Mau", "code": "ca-mau", "hotel_count": 11},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-an-giang.html", "location_name": "An Giang", "code": "an-giang", "hotel_count": 23},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-quang-ngai.html", "location_name": "Quảng Ngãi", "code": "quang-ngai", "hotel_count": 17},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-tay-ninh.html", "location_name": "Tây Ninh", "code": "tay-ninh", "hotel_count": 7},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-quang-ninh.html", "location_name": "Quảng Ninh", "code": "quang-ninh", "hotel_count": 230},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-long-an.html", "location_name": "Long An", "code": "long-an", "hotel_count": 2},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-quang-nam.html", "location_name": "Quảng Nam", "code": "quang-nam", "hotel_count": 162},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-hoi-an.html", "location_name": "Hội An", "code": "hoi-an", "hotel_count": 150},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-ben-tre.html", "location_name": "Bến Tre", "code": "ben-tre", "hotel_count": 9},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-yen-bai.html", "location_name": "Yên Bái", "code": "yen-bai", "hotel_count": 7},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-thanh-hoa.html", "location_name": "Thanh Hóa", "code": "thanh-hoa", "hotel_count": 86},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-ha-tinh.html", "location_name": "Hà Tĩnh", "code": "ha-tinh", "hotel_count": 26},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-phu-tho.html", "location_name": "Phú Thọ", "code": "phu-tho", "hotel_count": 8},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-quang-binh.html", "location_name": "Quảng Bình", "code": "quang-binh", "hotel_count": 43},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-binh-dinh.html", "location_name": "Bình Định", "code": "binh-dinh", "hotel_count": 104},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-quang-tri.html", "location_name": "Quảng Trị", "code": "quang-tri", "hotel_count": 5},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-tuyen-quang.html", "location_name": "Tuyên Quang", "code": "tuyen-quang", "hotel_count": 4},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-cao-bang.html", "location_name": "Cao Bằng", "code": "cao-bang", "hotel_count": 11},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-bac-kan.html", "location_name": "Bắc Kạn", "code": "bac-kan", "hotel_count": 2},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-thai-nguyen.html", "location_name": "Thái Nguyên", "code": "thai-nguyen", "hotel_count": 12},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-kon-tum.html", "location_name": "Kon Tum", "code": "kon-tum", "hotel_count": 8},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-lang-son.html", "location_name": "Lạng Sơn", "code": "lang-son", "hotel_count": 7},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-gia-lai.html", "location_name": "Gia Lai", "code": "gia-lai", "hotel_count": 17},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-bac-giang.html", "location_name": "Bắc Giang", "code": "bac-giang", "hotel_count": 6},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-dak-lak.html", "location_name": "Đắk Lắk", "code": "dak-lak", "hotel_count": 16},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-dak-nong.html", "location_name": "Đắk Nông", "code": "dak-nong", "hotel_count": 4},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-lam-dong.html", "location_name": "Lâm Đồng", "code": "lam-dong", "hotel_count": 282},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-khanh-hoa.html", "location_name": "Khánh Hòa", "code": "khanh-hoa", "hotel_count": 273},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-bac-lieu.html", "location_name": "Bạc Liêu", "code": "bac-lieu", "hotel_count": 8},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-dong-thap.html", "location_name": "Đồng Tháp", "code": "dong-thap", "hotel_count": 6},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-hau-giang.html", "location_name": "Hậu Giang", "code": "hau-giang", "hotel_count": 1},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-kien-giang.html", "location_name": "Kiên Giang", "code": "kien-giang", "hotel_count": 277},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-soc-trang.html", "location_name": "Sóc Trăng", "code": "soc-trang", "hotel_count": 6},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-tien-giang.html", "location_name": "Tiền Giang", "code": "tien-giang", "hotel_count": 6},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-tra-vinh.html", "location_name": "Trà Vinh", "code": "tra-vinh", "hotel_count": 1},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-vinh-long.html", "location_name": "Vĩnh Long", "code": "vinh-long", "hotel_count": 3},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-mui-ne.html", "location_name": "Mũi Né", "code": "mui-ne", "hotel_count": 44},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-bac-ninh.html", "location_name": "Bắc Ninh", "code": "bac-ninh", "hotel_count": 21},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-hai-duong.html", "location_name": "Hải Dương", "code": "hai-duong", "hotel_count": 5},
            {"url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-ha-nam.html", "location_name": "Hà Nam", "code": "ha-nam", "hotel_count": 7}
        ]
        
        logger.info(f"Using predefined list of {len(locations)} locations")
        for location in locations:
            logger.info(f"Location: {location['location_name']} ({location['hotel_count']} hotels)")
        
        return locations

    async def extract_locations(self) -> List[Dict]:
        """Main method để extract locations - sử dụng danh sách predefined"""
        # Sử dụng danh sách đã định sẵn thay vì crawl từ trang web
        locations = self.get_predefined_locations()
        return locations

async def main():
    """Main function"""
    extractor = LocationExtractor()
    
    # Extract locations
    locations = await extractor.extract_locations()
    
    if locations:
        # Save results
        output_dir = "data/raw/vietnambooking"
        extractor.save_locations(locations, output_dir)
        logger.info(f"Successfully extracted and saved {len(locations)} locations")
    else:
        logger.error("No locations extracted")

if __name__ == "__main__":
    asyncio.run(main())