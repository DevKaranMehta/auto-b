import os
import asyncio
import random
from typing import List, Dict, Any
import re
import logging
from openai import OpenAI

# Setup logging - FIXED LOGGER
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIContentService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found. AI features will not work.")
            self.client = None
        else:
            # FIXED: Use new OpenAI v1.0+ client initialization
            self.client = OpenAI(api_key=self.api_key)
            logger.info("✅ AI Service initialized successfully with OpenAI v1.0+")
    
    def _create_slug(self, title: str) -> str:
        """Create URL-friendly slug from title"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    async def _make_openai_request(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Make request to OpenAI API with new v1.0+ syntax"""
        if not self.client:
            raise Exception("OpenAI API key not configured")
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert blockchain and cryptocurrency journalist writing for BlockchainLatestNews.com. Write professional, informative, and engaging content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"AI service error: {str(e)}")
    
    def _make_openai_request_sync(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Synchronous version for non-async contexts"""
        if not self.client:
            raise Exception("OpenAI API key not configured")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert blockchain and cryptocurrency journalist writing for BlockchainLatestNews.com. Write professional, informative, and engaging content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"AI service error: {str(e)}")
    
    async def generate_blog_content(self, topic: str, category: str = "Technology") -> Dict[str, Any]:
        """Generate complete blog content"""
        try:
            prompt = f"""
            Write a comprehensive blog post about: {topic}
            Category: {category}
            
            Requirements:
            1. Professional blockchain/crypto journalism style
            2. 800-1200 words
            3. Include technical details but make it accessible
            4. Add market insights and implications
            5. Use HTML formatting (h2, h3, p, ul, li, strong, em)
            6. Include current trends and future outlook
            7. Write for both beginners and experienced crypto users
            
            Structure:
            - Engaging introduction
            - 3-4 main sections with h2 headers
            - Technical analysis where relevant
            - Market implications
            - Future outlook/conclusion
            
            Write the complete article content with proper HTML formatting.
            """
            
            content = await self._make_openai_request(prompt, max_tokens=2500)
            
            # Generate title - FIXED: Limit title length
            title_prompt = f"Create a compelling, SEO-optimized title for a blog post about: {topic}. Make it 50-70 characters, professional, and clickable for {category} category. Return ONLY the title."
            title = await self._make_openai_request(title_prompt, max_tokens=100)
            
            # Generate meta description - FIXED: Limit to 250 characters max
            meta_desc_prompt = f"Create a meta description (MAX 250 characters) for: {title}. Focus on key benefits and include relevant keywords. Return ONLY the description."
            meta_description = await self._make_openai_request(meta_desc_prompt, max_tokens=150)
            
            # Generate keywords - FIXED: Limit to 400 characters max
            keywords_prompt = f"Generate 5-8 SEO keywords for: {title} in {category} category. Return ONLY as comma-separated list (MAX 400 characters)."
            keywords = await self._make_openai_request(keywords_prompt, max_tokens=100)
            
            # FIXED: Ensure proper string formatting
            title_clean = title.strip().strip('"').strip("'")
            meta_description_clean = meta_description.strip().strip('"').strip("'")
            keywords_clean = keywords.strip().strip('"').strip("'")
            
            # FIXED: Ensure lengths are within database limits
            if len(title_clean) > 255:
                title_clean = title_clean[:252] + "..."
            
            if len(meta_description_clean) > 300:
                meta_description_clean = meta_description_clean[:297] + "..."
            
            if len(keywords_clean) > 500:
                keywords_clean = keywords_clean[:497] + "..."
            
            # FIXED: Create proper tags string (not individual characters)
            tags_list = [kw.strip() for kw in keywords_clean.split(",")[:5]]
            tags_string = ", ".join(tags_list)
            
            return {
                "title": title_clean,
                "content": content,
                "meta_description": meta_description_clean,
                "meta_keywords": keywords_clean,
                "slug": self._create_slug(title_clean),
                "category": category,
                "tags": tags_string,  # FIXED: Return as string, not list
                "ai_prompt": f"Topic: {topic}, Category: {category}"
            }
            
        except Exception as e:
            logger.error(f"Error generating blog content: {e}")
            raise
    
    async def generate_trending_topics(self) -> List[str]:
        """Generate trending cryptocurrency topics"""
        try:
            prompt = """
            Generate 10 trending cryptocurrency and blockchain topics that would make great blog posts.
            Focus on:
            - Current market trends
            - New technologies
            - Regulatory developments
            - DeFi innovations
            - NFT trends
            - Major crypto news
            
            Return as a simple list, one topic per line, no numbers or bullets.
            Make them specific and newsworthy.
            """
            
            response = await self._make_openai_request(prompt, max_tokens=500)
            topics = [topic.strip() for topic in response.split('\n') if topic.strip()]
            return topics[:10]
            
        except Exception as e:
            logger.error(f"Error generating trending topics: {e}")
            return [
                "Bitcoin ETF Latest Developments",
                "Ethereum 2.0 Staking Rewards Analysis",
                "DeFi Yield Farming Strategies 2025",
                "NFT Market Recovery Trends",
                "Central Bank Digital Currencies Update"
            ]
    
    def generate_trending_topics_sync(self) -> List[str]:
        """Synchronous version for scheduler"""
        try:
            prompt = """
            Generate 10 trending cryptocurrency and blockchain topics that would make great blog posts.
            Focus on:
            - Current market trends
            - New technologies
            - Regulatory developments
            - DeFi innovations
            - NFT trends
            - Major crypto news
            
            Return as a simple list, one topic per line, no numbers or bullets.
            Make them specific and newsworthy.
            """
            
            response = self._make_openai_request_sync(prompt, max_tokens=500)
            topics = [topic.strip() for topic in response.split('\n') if topic.strip()]
            return topics[:10]
            
        except Exception as e:
            logger.error(f"Error generating trending topics: {e}")
            return [
                "Bitcoin ETF Latest Developments",
                "Ethereum 2.0 Staking Rewards Analysis",
                "DeFi Yield Farming Strategies 2025",
                "NFT Market Recovery Trends",
                "Central Bank Digital Currencies Update"
            ]
    
    async def generate_seo_title(self, content: str, category: str) -> str:
        """Generate SEO-optimized title"""
        try:
            prompt = f"""
            Create an SEO-optimized title for a {category} blog post about blockchain/cryptocurrency.
            
            Content preview: {content[:500]}...
            
            Requirements:
            - 50-70 characters ideal length
            - Include relevant keywords
            - Compelling and clickable
            - Professional tone
            - Specific to blockchain/crypto industry
            
            Return only the title, no quotes or extra text.
            """
            
            response = await self._make_openai_request(prompt, max_tokens=100)
            title = response.strip().strip('"').strip("'")
            
            # FIXED: Ensure title is not too long
            if len(title) > 255:
                title = title[:252] + "..."
            
            return title
            
        except Exception as e:
            logger.error(f"Error generating SEO title: {e}")
            return f"Latest {category} News and Analysis"
    
    async def generate_meta_description(self, title: str, content: str) -> str:
        """Generate meta description"""
        try:
            prompt = f"""
            Create an SEO meta description for this blog post:
            
            Title: {title}
            Content preview: {content[:300]}...
            
            Requirements:
            - 150-250 characters ideal length
            - Include key terms
            - Compelling call-to-action
            - Summarize main value
            - Professional blockchain/crypto tone
            
            Return only the description, no quotes.
            """
            
            response = await self._make_openai_request(prompt, max_tokens=150)
            description = response.strip().strip('"').strip("'")
            
            # FIXED: Ensure description is not too long
            if len(description) > 300:
                description = description[:297] + "..."
            
            return description
            
        except Exception as e:
            logger.error(f"Error generating meta description: {e}")
            return f"Discover the latest insights about {title}. Expert analysis and trends in blockchain technology."
    
    async def generate_meta_keywords(self, title: str, content: str, category: str) -> str:
        """Generate meta keywords"""
        try:
            prompt = f"""
            Generate SEO keywords for this blockchain/crypto blog post:
            
            Title: {title}
            Category: {category}
            Content preview: {content[:200]}...
            
            Requirements:
            - 5-10 relevant keywords
            - Mix of specific and general terms
            - Comma-separated format
            - Focus on blockchain/crypto terms
            - Include category-specific keywords
            - MAX 400 characters total
            
            Return only keywords separated by commas.
            """
            
            response = await self._make_openai_request(prompt, max_tokens=100)
            keywords = response.strip().strip('"').strip("'")
            
            # FIXED: Ensure keywords are not too long
            if len(keywords) > 500:
                keywords = keywords[:497] + "..."
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error generating keywords: {e}")
            return f"blockchain, cryptocurrency, {category.lower()}, bitcoin, crypto news, digital assets"
