import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, quote_plus
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
import random
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobPosting:
    """Data class for job posting information"""
    company: str
    title: str
    location: str
    date_posted: str
    url: str
    platform: str
    description: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

@dataclass
class HiringInsight:
    """Data class for hiring insights"""
    company: str
    hiring_velocity: str  # 'high', 'medium', 'low'
    job_growth_trend: float  # percentage change
    avg_days_to_fill: int
    most_common_roles: List[str]
    salary_range: Dict[str, str]
    locations: List[str]
    urgency_indicators: List[str]

class HiringCompaniesAnalyzer:
    """Analyzes job postings to identify currently hiring companies with real-time insights"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.job_postings = []
        self.hiring_insights = {}
        
    def scrape_linkedin_jobs(self, keywords: str = "developer OR engineer OR analyst OR manager OR designer OR consultant OR specialist ", location: str = "India", max_pages: int = 2) -> List[JobPosting]:
        """Scrape job postings from LinkedIn (simplified approach due to anti-bot measures)"""
        jobs = []
        
        try:
            # LinkedIn requires authentication for full access, so we'll use a simplified approach
            # In production, you'd want to use LinkedIn's official API
            base_url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': keywords,
                'location': location,
                'f_TPR': 'r86400',  # Past 24 hours
                'f_JT': 'F',  # Full-time
                'start': 0
            }
            
            for page in range(max_pages):
                params['start'] = page * 25
                
                try:
                    response = self.session.get(base_url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_cards = soup.find_all('div', class_='base-card')
                    
                    for card in job_cards[:10]:  # Limit to avoid being blocked
                        try:
                            title_elem = card.find('h3', class_='base-search-card__title')
                            title = title_elem.get_text(strip=True) if title_elem else "N/A"
                            
                            company_elem = card.find('h4', class_='base-search-card__subtitle')
                            company = company_elem.get_text(strip=True) if company_elem else "N/A"
                            
                            location_elem = card.find('span', class_='job-search-card__location')
                            location_text = location_elem.get_text(strip=True) if location_elem else "N/A"
                            
                            link_elem = card.find('a', class_='base-card__full-link')
                            job_url = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                            
                            job = JobPosting(
                                company=company,
                                title=title,
                                location=location_text,
                                date_posted="Recent",
                                url=job_url,
                                platform="LinkedIn",
                                job_type="Full-time"
                            )
                            jobs.append(job)
                            
                        except Exception as e:
                            logger.warning(f"Error parsing LinkedIn job card: {e}")
                            continue
                    
                    time.sleep(random.uniform(2, 4))  # Longer delay for LinkedIn
                    
                except Exception as e:
                    logger.warning(f"Error accessing LinkedIn page {page}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
            
        return jobs
    
    def scrape_indeed_jobs(self, keywords: str = "developer OR engineer OR analyst OR manager OR designer OR consultant OR specialist", location: str = "India", max_pages: int = 3) -> List[JobPosting]:
        """Enhanced Indeed scraping with more data extraction"""
        jobs = []
        
        try:
            for page in range(max_pages):
                url = f"https://www.indeed.com/jobs?q={quote_plus(keywords)}&l={quote_plus(location)}&fromage=1&start={page * 10}"
                
                response = self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                for card in job_cards:
                    try:
                        # Extract job details
                        title_elem = card.find('h2', class_='jobTitle')
                        title = title_elem.find('a').get_text(strip=True) if title_elem else "N/A"
                        
                        company_elem = card.find('span', class_='companyName')
                        company = company_elem.get_text(strip=True) if company_elem else "N/A"
                        
                        location_elem = card.find('div', class_='companyLocation')
                        location_text = location_elem.get_text(strip=True) if location_elem else "N/A"
                        
                        date_elem = card.find('span', class_='date')
                        date_posted = date_elem.get_text(strip=True) if date_elem else "N/A"
                        
                        # Get job URL
                        job_url = ""
                        if title_elem and title_elem.find('a'):
                            job_url = urljoin("https://www.indeed.com", title_elem.find('a')['href'])
                        
                        # Extract salary if available
                        salary_elem = card.find('span', class_='estimated-salary')
                        salary = salary_elem.get_text(strip=True) if salary_elem else None
                        
                        # Extract job type and experience level
                        job_type = "Full-time"  # Default
                        experience_level = "Not specified"
                        
                        # Look for urgency indicators
                        urgency_indicators = []
                        if "urgent" in title.lower() or "immediate" in title.lower():
                            urgency_indicators.append("Urgent hiring")
                        if "new" in date_posted.lower():
                            urgency_indicators.append("Recently posted")
                        
                        job = JobPosting(
                            company=company,
                            title=title,
                            location=location_text,
                            date_posted=date_posted,
                            url=job_url,
                            platform="Indeed",
                            salary=salary,
                            job_type=job_type,
                            experience_level=experience_level
                        )
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing job card: {e}")
                        continue
                
                # Add delay between requests
                time.sleep(random.uniform(1, 3))
                
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
            
        return jobs
    
    def analyze_hiring_velocity(self, company_jobs: List[JobPosting]) -> str:
        """Analyze hiring velocity based on job posting frequency"""
        job_count = len(company_jobs)
        
        if job_count >= 10:
            return "high"
        elif job_count >= 5:
            return "medium"
        else:
            return "low"
    
    def extract_urgency_indicators(self, jobs: List[JobPosting]) -> List[str]:
        """Extract urgency indicators from job postings"""
        indicators = []
        
        for job in jobs:
            if any(word in job.title.lower() for word in ["urgent", "immediate", "asap"]):
                indicators.append("Urgent hiring needs")
            if "today" in job.date_posted.lower() or "1 day" in job.date_posted.lower():
                indicators.append("Very recent postings")
            if job.salary and "$" in job.salary:
                indicators.append("Competitive salary offered")
        
        return list(set(indicators))
    
    def generate_hiring_insights(self, company_name: str, company_jobs: List[JobPosting]) -> HiringInsight:
        """Generate comprehensive hiring insights for a company"""
        
        # Analyze hiring velocity
        velocity = self.analyze_hiring_velocity(company_jobs)
        
        # Extract most common roles
        role_counts = defaultdict(int)
        for job in company_jobs:
            # Simplify job titles to common roles
            title_lower = job.title.lower()
            if "engineer" in title_lower:
                role_counts["Software Engineer"] += 1
            elif "developer" in title_lower:
                role_counts["Developer"] += 1
            elif "manager" in title_lower:
                role_counts["Manager"] += 1
            elif "analyst" in title_lower:
                role_counts["Analyst"] += 1
            else:
                role_counts[job.title] += 1
        
        most_common_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        most_common_roles = [role[0] for role in most_common_roles]
        
        # Extract locations
        locations = list(set([job.location for job in company_jobs if job.location != "N/A"]))[:5]
        
        # Extract salary information
        salaries = [job.salary for job in company_jobs if job.salary]
        salary_range = {"min": "Not specified", "max": "Not specified"}
        if salaries:
            salary_range = {"range": f"{len(salaries)} positions with salary info"}
        
        # Extract urgency indicators
        urgency_indicators = self.extract_urgency_indicators(company_jobs)
        
        return HiringInsight(
            company=company_name,
            hiring_velocity=velocity,
            job_growth_trend=len(company_jobs) * 5.0,  # Simplified growth calculation
            avg_days_to_fill=30,  # Estimated average
            most_common_roles=most_common_roles,
            salary_range=salary_range,
            locations=locations,
            urgency_indicators=urgency_indicators
        )
    
    def analyze_hiring_companies(self, keywords: str = "developer OR engineer OR analyst OR manager OR designer OR consultant OR specialist", location: str = "India") -> Dict:
        """Enhanced analysis with real-time insights"""
        logger.info("Starting real-time hiring companies analysis...")
        
        all_jobs = []
        
        # Scrape from multiple platforms with real-time focus
        logger.info("Scraping LinkedIn for recent postings...")
        linkedin_jobs = self.scrape_linkedin_jobs(keywords, location, max_pages=2)
        all_jobs.extend(linkedin_jobs)
        
        logger.info("Scraping Indeed for latest jobs...")
        indeed_jobs = self.scrape_indeed_jobs(keywords, location, max_pages=3)
        all_jobs.extend(indeed_jobs)
        
        logger.info("Scraping Glassdoor...")
        glassdoor_jobs = self.scrape_glassdoor_jobs(keywords, location, max_pages=2)
        all_jobs.extend(glassdoor_jobs)
        
        logger.info("Scraping Monster...")
        monster_jobs = self.scrape_monster_jobs(keywords, location)
        all_jobs.extend(monster_jobs)
        
        # Analyze companies with insights
        company_stats = {}
        company_insights = {}
        
        # Group jobs by company
        company_jobs = defaultdict(list)
        for job in all_jobs:
            company = job.company.strip()
            if company and company != "N/A":
                company_jobs[company].append(job)
        
        # Generate insights for each company
        for company, jobs in company_jobs.items():
            # Basic stats
            company_stats[company] = {
                'job_count': len(jobs),
                'positions': [job.title for job in jobs],
                'locations': list(set([job.location for job in jobs])),
                'platforms': list(set([job.platform for job in jobs])),
                'recent_postings': [{
                    'title': job.title,
                    'location': job.location,
                    'date': job.date_posted,
                    'url': job.url,
                    'platform': job.platform,
                    'salary': job.salary,
                    'job_type': job.job_type
                } for job in jobs]
            }
            
            # Generate hiring insights
            insight = self.generate_hiring_insights(company, jobs)
            company_insights[company] = {
                'hiring_velocity': insight.hiring_velocity,
                'job_growth_trend': insight.job_growth_trend,
                'most_common_roles': insight.most_common_roles,
                'salary_info': insight.salary_range,
                'top_locations': insight.locations,
                'urgency_indicators': insight.urgency_indicators,
                'hiring_status': self.get_hiring_status(insight.hiring_velocity, len(jobs))
            }
        
        # Sort companies by job count and hiring velocity
        sorted_companies = dict(sorted(company_stats.items(), 
                                     key=lambda x: (x[1]['job_count'], 
                                                   self.get_velocity_score(company_insights.get(x[0], {}).get('hiring_velocity', 'low'))), 
                                     reverse=True))
        
        # Generate market insights
        market_insights = self.generate_market_insights(all_jobs, company_insights)
        
        result = {
            'total_jobs_found': len(all_jobs),
            'total_companies': len(company_stats),
            'search_keywords': keywords,
            'search_location': location,
            'analysis_date': datetime.now().isoformat(),
            'companies': sorted_companies,
            'company_insights': company_insights,
            'top_hiring_companies': list(sorted_companies.keys())[:20],
            'market_insights': market_insights,
            'real_time_data': {
                'linkedin_jobs': len(linkedin_jobs),
                'indeed_jobs': len(indeed_jobs),
                'glassdoor_jobs': len(glassdoor_jobs),
                'monster_jobs': len(monster_jobs),
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        logger.info(f"Real-time analysis complete. Found {len(all_jobs)} jobs from {len(company_stats)} companies")
        
        return result
    
    def get_velocity_score(self, velocity: str) -> int:
        """Convert velocity to numeric score for sorting"""
        scores = {'high': 3, 'medium': 2, 'low': 1}
        return scores.get(velocity, 0)
    
    def get_hiring_status(self, velocity: str, job_count: int) -> str:
        """Determine hiring status based on velocity and job count"""
        if velocity == 'high' and job_count >= 10:
            return "🔥 Aggressively Hiring"
        elif velocity == 'high' or job_count >= 7:
            return "📈 Actively Hiring"
        elif velocity == 'medium' or job_count >= 3:
            return "✅ Currently Hiring"
        else:
            return "📋 Limited Openings"
    
    def generate_market_insights(self, all_jobs: List[JobPosting], company_insights: Dict) -> Dict:
        """Generate overall market insights"""
        
        # Platform distribution
        platform_counts = defaultdict(int)
        for job in all_jobs:
            platform_counts[job.platform] += 1
        
        # Most in-demand roles
        role_counts = defaultdict(int)
        for job in all_jobs:
            title_lower = job.title.lower()
            if "engineer" in title_lower:
                role_counts["Software Engineer"] += 1
            elif "developer" in title_lower:
                role_counts["Developer"] += 1
            elif "manager" in title_lower:
                role_counts["Manager"] += 1
            elif "analyst" in title_lower:
                role_counts["Analyst"] += 1
        
        top_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # High-velocity companies
        high_velocity_companies = [
            company for company, insight in company_insights.items() 
            if insight.get('hiring_velocity') == 'high'
        ]
        
        return {
            'platform_distribution': dict(platform_counts),
            'most_in_demand_roles': dict(top_roles),
            'high_velocity_companies_count': len(high_velocity_companies),
            'high_velocity_companies': high_velocity_companies[:10],
            'market_activity': 'High' if len(all_jobs) > 50 else 'Medium' if len(all_jobs) > 20 else 'Low',
            'trending_locations': self.get_trending_locations(all_jobs)
        }
    
    def get_trending_locations(self, jobs: List[JobPosting]) -> List[str]:
        """Get trending hiring locations"""
        location_counts = defaultdict(int)
        for job in jobs:
            if job.location and job.location != "N/A":
                location_counts[job.location] += 1
        
        return [loc for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    def scrape_glassdoor_jobs(self, keywords: str = "developer OR engineer OR analyst OR manager OR designer OR consultant OR specialist", location: str = "India", max_pages: int = 2) -> List[JobPosting]:
        """Scrape job postings from Glassdoor"""
        jobs = []
        
        try:
            # Note: Glassdoor has anti-bot measures, so this is a simplified approach
            base_url = "https://www.glassdoor.com/Job/jobs.htm"
            params = {
                'sc.keyword': keywords,
                'locT': 'C',
                'locId': '1',
                'jobType': '',
                'fromAge': 1,
                'minSalary': 0,
                'includeNoSalaryJobs': 'true',
                'radius': 25,
                'cityId': -1,
                'minRating': 0.0,
                'industryId': -1,
                'sgocId': -1,
                'seniorityType': '',
                'companyId': -1,
                'employerSizes': '',
                'applicationType': '',
                'remoteWorkType': 0
            }
            
            response = self.session.get(base_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Glassdoor uses dynamic loading, so we'll look for basic job elements
            job_elements = soup.find_all('li', class_='react-job-listing')
            
            for job_elem in job_elements[:20]:  # Limit to first 20 jobs
                try:
                    # Extract basic information (structure may vary)
                    title_elem = job_elem.find('a', {'data-test': 'job-title'})
                    title = title_elem.get_text(strip=True) if title_elem else "N/A"
                    
                    company_elem = job_elem.find('span', {'data-test': 'employer-name'})
                    company = company_elem.get_text(strip=True) if company_elem else "N/A"
                    
                    location_elem = job_elem.find('span', {'data-test': 'job-location'})
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"
                    
                    job_url = ""
                    if title_elem and title_elem.find('a'):
                        job_url = urljoin("https://www.glassdoor.com", title_elem.find('a')['href'])
                    
                    job = JobPosting(
                        company=company,
                        title=title,
                        location=location_text,
                        date_posted="Recent",
                        url=job_url,
                        platform="Glassdoor"
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    logger.warning(f"Error parsing Glassdoor job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Glassdoor: {e}")
            
        return jobs
    
    def scrape_monster_jobs(self, keywords: str = "developer OR engineer OR analyst OR manager OR designer OR consultant OR specialist", location: str = "India") -> List[JobPosting]:
        """Scrape job postings from Monster"""
        jobs = []
        
        try:
            url = f"https://www.monster.com/jobs/search/?q={quote_plus(keywords)}&where={quote_plus(location)}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('section', class_='card-content')
            
            for card in job_cards:
                try:
                    title_elem = card.find('h2', class_='title')
                    title = title_elem.find('a').get_text(strip=True) if title_elem and title_elem.find('a') else "N/A"
                    
                    company_elem = card.find('div', class_='company')
                    company = company_elem.find('span').get_text(strip=True) if company_elem and company_elem.find('span') else "N/A"
                    
                    location_elem = card.find('div', class_='location')
                    location_text = location_elem.find('span').get_text(strip=True) if location_elem and location_elem.find('span') else "N/A"
                    
                    job_url = ""
                    if title_elem and title_elem.find('a'):
                        job_url = urljoin("https://www.monster.com", title_elem.find('a')['href'])
                    
                    job = JobPosting(
                        company=company,
                        title=title,
                        location=location_text,
                        date_posted="Recent",
                        url=job_url,
                        platform="Monster"
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    logger.warning(f"Error parsing Monster job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Monster: {e}")
            
        return jobs
    
    def save_analysis_results(self, results: Dict, filename: str = None) -> str:
        """Save analysis results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hiring_analysis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filename}")
        return filename

# Example usage
if __name__ == "__main__":
    analyzer = HiringCompaniesAnalyzer()
    
    # Analyze hiring companies with real-time insights
    results = analyzer.analyze_hiring_companies(
        keywords="developer OR engineer OR analyst OR manager OR designer OR consultant OR specialist",
        location="India"
    )
    
    # Save results
    filename = analyzer.save_analysis_results(results)
    
    # Print insights
    print(f"\n🔍 Real-Time Hiring Analysis Results:")
    print(f"📊 Total Jobs Found: {results['total_jobs_found']}")
    print(f"🏢 Companies Hiring: {results['total_companies']}")
    print(f"📈 Market Activity: {results['market_insights']['market_activity']}")
    
    print(f"\n🔥 Top Hiring Companies:")
    for i, company in enumerate(results['top_hiring_companies'][:5], 1):
        job_count = results['companies'][company]['job_count']
        status = results['company_insights'].get(company, {}).get('hiring_status', 'Unknown')
        print(f"{i}. {company} - {job_count} jobs {status}")
    
    print(f"\n📍 Trending Locations:")
    for loc in results['market_insights']['trending_locations']:
        print(f"• {loc}")
