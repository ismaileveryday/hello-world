import re
import requests
from packaging import version
from typing import Tuple, Optional, Dict
from bs4 import BeautifulSoup
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VersionChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Tool-Version-Checker/1.0'
        })
    
    def normalize_version(self, version_str: str) -> str:
        """Normalize version string for comparison"""
        # Remove common prefixes and suffixes
        version_str = re.sub(r'^[vV]', '', version_str)
        version_str = re.sub(r'[-_].*$', '', version_str)
        
        # Handle special cases
        if 'SQL Server' in version_str:
            # Extract year from SQL Server versions
            match = re.search(r'(\d{4})', version_str)
            if match:
                return match.group(1)
        
        # Extract semantic version pattern
        match = re.search(r'(\d+(?:\.\d+)*)', version_str)
        if match:
            return match.group(1)
        
        return version_str
    
    def compare_versions(self, current: str, latest: str) -> bool:
        """Compare two versions and return True if current is outdated"""
        try:
            current_norm = self.normalize_version(current)
            latest_norm = self.normalize_version(latest)
            
            # Use packaging library for semantic version comparison
            return version.parse(current_norm) < version.parse(latest_norm)
        except Exception as e:
            logger.warning(f"Version comparison failed: {e}")
            # Fallback to string comparison
            return current_norm != latest_norm
    
    def fetch_latest_version_github(self, api_url: str) -> Optional[str]:
        """Fetch latest version from GitHub API"""
        try:
            response = self.session.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            tag_name = data.get('tag_name', '')
            return self.normalize_version(tag_name)
        except Exception as e:
            logger.error(f"Failed to fetch from GitHub API {api_url}: {e}")
            return None
    
    def fetch_latest_version_website(self, url: str, pattern: str) -> Optional[str]:
        """Fetch latest version from official website using regex pattern"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            
            if pattern:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    return self.normalize_version(match.group(1))
            
            # Fallback: look for common version patterns
            version_patterns = [
                r'version\s+(\d+(?:\.\d+)*)',
                r'v(\d+(?:\.\d+)*)',
                r'(\d+(?:\.\d+)+)',
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    return self.normalize_version(match.group(1))
                    
        except Exception as e:
            logger.error(f"Failed to fetch from website {url}: {e}")
            
        return None
    
    def get_latest_version(self, tool_name: str, source_info: Dict) -> Optional[str]:
        """Get the latest version for a tool based on source information"""
        source_type = source_info.get('source_type')
        source_url = source_info.get('source_url')
        version_pattern = source_info.get('version_pattern')
        
        if source_type == 'github':
            return self.fetch_latest_version_github(source_url)
        elif source_type == 'official_site':
            return self.fetch_latest_version_website(source_url, version_pattern)
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return None
    
    def get_upgrade_instructions(self, tool_name: str, current_version: str, latest_version: str) -> Dict[str, str]:
        """Get upgrade instructions and version improvements"""
        instructions = {
            'upgrade_steps': '',
            'version_improvements': '',
            'documentation_links': []
        }
        
        # Tool-specific upgrade instructions
        if 'SQL Server' in tool_name:
            instructions.update({
                'upgrade_steps': '''
1. Backup your current databases
2. Download SQL Server {} from Microsoft
3. Run the installer and follow the upgrade wizard
4. Test your applications after upgrade
5. Update connection strings if needed
                '''.format(latest_version),
                'version_improvements': 'Enhanced security, performance improvements, new T-SQL features',
                'documentation_links': [
                    'https://docs.microsoft.com/en-us/sql/database-engine/install-windows/upgrade-sql-server',
                    'https://docs.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-ver15'
                ]
            })
        
        elif 'Python' in tool_name:
            instructions.update({
                'upgrade_steps': '''
1. Check compatibility of your packages: pip list --outdated
2. Create a backup of your virtual environment
3. Download Python {} from python.org
4. Install the new version
5. Recreate your virtual environment
6. Reinstall packages: pip install -r requirements.txt
                '''.format(latest_version),
                'version_improvements': 'Performance improvements, security fixes, new language features',
                'documentation_links': [
                    'https://docs.python.org/3/whatsnew/',
                    'https://www.python.org/downloads/'
                ]
            })
        
        elif 'Node.js' in tool_name:
            instructions.update({
                'upgrade_steps': '''
1. Check current Node.js version: node --version
2. Backup your package-lock.json
3. Download Node.js {} from nodejs.org
4. Install the new version
5. Clear npm cache: npm cache clean --force
6. Reinstall dependencies: npm install
                '''.format(latest_version),
                'version_improvements': 'V8 engine updates, npm improvements, security patches',
                'documentation_links': [
                    'https://nodejs.org/en/blog/',
                    'https://github.com/nodejs/node/blob/main/CHANGELOG.md'
                ]
            })
        
        elif 'Java' in tool_name:
            instructions.update({
                'upgrade_steps': '''
1. Check current Java version: java -version
2. Download JDK {} from Oracle or OpenJDK
3. Install the new version
4. Update JAVA_HOME environment variable
5. Update PATH to point to new Java installation
6. Test your applications
                '''.format(latest_version),
                'version_improvements': 'Security updates, performance enhancements, new APIs',
                'documentation_links': [
                    'https://www.oracle.com/java/technologies/javase-downloads.html',
                    'https://openjdk.java.net/'
                ]
            })
        
        elif '.NET' in tool_name:
            instructions.update({
                'upgrade_steps': '''
1. Check current .NET version: dotnet --version
2. Download .NET {} SDK from Microsoft
3. Install the new version
4. Update your project files (.csproj)
5. Update NuGet packages
6. Test and rebuild your applications
                '''.format(latest_version),
                'version_improvements': 'Performance improvements, new C# features, security updates',
                'documentation_links': [
                    'https://docs.microsoft.com/en-us/dotnet/',
                    'https://github.com/dotnet/core/releases'
                ]
            })
        
        elif 'Oracle Database' in tool_name:
            instructions.update({
                'upgrade_steps': '''
1. Backup your database using RMAN or Export
2. Review Oracle upgrade documentation
3. Download Oracle Database {} from Oracle
4. Run the Database Upgrade Assistant (DBUA)
5. Test your applications
6. Update statistics and optimize
                '''.format(latest_version),
                'version_improvements': 'New SQL features, performance optimizations, security enhancements',
                'documentation_links': [
                    'https://docs.oracle.com/en/database/',
                    'https://www.oracle.com/database/technologies/'
                ]
            })
        
        else:
            # Generic instructions
            instructions.update({
                'upgrade_steps': f'''
1. Check current version of {tool_name}
2. Backup your current configuration
3. Download version {latest_version} from official source
4. Follow the installation/upgrade guide
5. Test functionality after upgrade
                ''',
                'version_improvements': 'Bug fixes, security updates, performance improvements',
                'documentation_links': ['Check official documentation for specific upgrade steps']
            })
        
        return instructions

# Create global version checker instance
version_checker = VersionChecker()