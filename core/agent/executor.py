"""
JARVIS Tool Executor - Tool implementations for workers
20+ tools across File, Code, Web, System, and Data categories
Optimized for i3/12GB with aggressive caching
"""

import os
import re
import json
import asyncio
import logging
import subprocess
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ToolExecutor:
    """
    Tool execution engine
    Provides 20+ tools for agent workers
    """
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._init_tools()
        
        # Tool execution cache
        self._cache: Dict[str, Any] = {}
        
    def _init_tools(self):
        """Initialize all available tools"""
        # File tools
        self.tools['read_file'] = self._read_file
        self.tools['write_file'] = self._write_file
        self.tools['search_files'] = self._search_files
        self.tools['list_directory'] = self._list_directory
        self.tools['analyze_document'] = self._analyze_document
        
        # Code tools
        self.tools['generate_code'] = self._generate_code
        self.tools['edit_file'] = self._edit_file
        self.tools['execute_python'] = self._execute_python
        self.tools['analyze_code'] = self._analyze_code
        self.tools['debug_code'] = self._debug_code
        
        # System tools
        self.tools['system_info'] = self._system_info
        self.tools['execute_command'] = self._execute_command
        self.tools['manage_process'] = self._manage_process
        self.tools['control_apps'] = self._control_apps
        
        # Web tools (async)
        self.tools['web_search'] = self._web_search
        self.tools['fetch_url'] = self._fetch_url
        
        # Data tools
        self.tools['analyze_csv'] = self._analyze_csv
        self.tools['create_chart'] = self._create_chart
        self.tools['extract_data'] = self._extract_data
        self.tools['compare_data'] = self._compare_data
        
        logger.info(f"Initialized {len(self.tools)} tools")
        
    # ==================== FILE TOOLS ====================
    
    async def _read_file(self, path: str, limit_lines: int = 100) -> Dict[str, Any]:
        """Read file content"""
        try:
            file_path = Path(path).expanduser()
            
            if not file_path.exists():
                return {'error': f'File not found: {path}'}
                
            # Check file size (limit for memory)
            size = file_path.stat().st_size
            if size > 10 * 1024 * 1024:  # 10MB limit
                return {'error': 'File too large (>10MB)'}
                
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                if limit_lines:
                    lines = f.readlines()[:limit_lines]
                    content = ''.join(lines)
                else:
                    content = f.read()
                    
            return {
                'success': True,
                'path': str(file_path),
                'content': content,
                'size': size,
                'lines': len(content.split('\n'))
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _write_file(self, path: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """Write file content"""
        try:
            file_path = Path(path).expanduser()
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup existing file
            if backup and file_path.exists():
                backup_path = file_path.with_suffix('.backup')
                backup_path.write_text(file_path.read_text())
                
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return {
                'success': True,
                'path': str(file_path),
                'size': len(content),
                'backed_up': backup and file_path.exists()
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _search_files(self, pattern: str, path: str = '.', max_results: int = 20) -> Dict[str, Any]:
        """Search files by pattern"""
        try:
            search_path = Path(path).expanduser()
            
            if not search_path.exists():
                return {'error': f'Path not found: {path}'}
                
            results = []
            
            # Convert glob pattern to regex
            if '*' in pattern:
                # Use glob
                files = list(search_path.rglob(pattern))
                results = [str(f) for f in files[:max_results]]
            else:
                # Search file content
                for file_path in search_path.rglob('*'):
                    if file_path.is_file() and file_path.stat().st_size < 1024 * 1024:  # <1MB
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if pattern.lower() in content.lower():
                                    results.append(str(file_path))
                                    if len(results) >= max_results:
                                        break
                        except:
                            continue
                            
            return {
                'success': True,
                'pattern': pattern,
                'path': str(search_path),
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _list_directory(self, path: str = '.', max_depth: int = 1) -> Dict[str, Any]:
        """List directory contents"""
        try:
            dir_path = Path(path).expanduser()
            
            if not dir_path.exists():
                return {'error': f'Path not found: {path}'}
                
            items = []
            
            for item in dir_path.iterdir():
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else 0
                }
                items.append(item_info)
                
            return {
                'success': True,
                'path': str(dir_path),
                'items': sorted(items, key=lambda x: (x['type'] != 'directory', x['name'])),
                'count': len(items)
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _analyze_document(self, path: str) -> Dict[str, Any]:
        """Analyze document structure"""
        try:
            file_path = Path(path).expanduser()
            
            if not file_path.exists():
                return {'error': f'File not found: {path}'}
                
            ext = file_path.suffix.lower()
            
            # Read content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            analysis = {
                'path': str(file_path),
                'size': len(content),
                'lines': content.count('\n') + 1,
                'extension': ext
            }
            
            # Language-specific analysis
            if ext == '.py':
                analysis['functions'] = len(re.findall(r'\bdef\s+\w+', content))
                analysis['classes'] = len(re.findall(r'\bclass\s+\w+', content))
                analysis['imports'] = len(re.findall(r'^(?:import|from)\s+', content, re.M))
            elif ext in ['.js', '.ts']:
                analysis['functions'] = len(re.findall(r'\bfunction\s+\w+|\bconst\s+\w+\s*=\s*(?:\(|async)', content))
            elif ext in ['.json']:
                try:
                    data = json.loads(content)
                    analysis['keys'] = len(data) if isinstance(data, dict) else len(data)
                except:
                    pass
                    
            return {
                'success': True,
                **analysis
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    # ==================== CODE TOOLS ====================
    
    async def _generate_code(self, prompt: str, language: str = 'python') -> Dict[str, Any]:
        """Generate code from prompt (placeholder - would use LLM)"""
        # In real implementation, this would call LLM
        # For now, return template
        
        templates = {
            'python': f'# Generated Python code\n# Prompt: {prompt[:50]}...\n\ndef generated_function():\n    """{prompt}"""\n    # TODO: Implement\n    pass\n',
            'javascript': f'// Generated JavaScript code\n// Prompt: {prompt[:50]}...\n\nfunction generatedFunction() {{\n    // TODO: Implement\n    console.log("{prompt[:30]}...");\n}}\n'
        }
        
        code = templates.get(language, templates['python'])
        
        return {
            'success': True,
            'language': language,
            'code': code,
            'prompt': prompt
        }
        
    async def _edit_file(self, file_path: str, changes: List[Dict]) -> Dict[str, Any]:
        """Apply edits to file"""
        try:
            path = Path(file_path).expanduser()
            
            # Read current content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original = content
            
            # Apply changes
            for change in changes:
                old = change.get('old', '')
                new = change.get('new', '')
                content = content.replace(old, new, 1)
                
            # Write back
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return {
                'success': True,
                'path': str(path),
                'changes_applied': len(changes),
                'diff_size': len(content) - len(original)
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code safely"""
        try:
            # Create temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
                
            # Execute with timeout
            result = subprocess.run(
                ['python', temp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Cleanup
            os.unlink(temp_path)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timeout', 'success': False}
        except Exception as e:
            return {'error': str(e), 'success': False}
            
    async def _analyze_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Analyze code structure"""
        try:
            analysis = {
                'language': language,
                'length': len(code),
                'lines': code.count('\n') + 1
            }
            
            if language == 'python':
                analysis['functions'] = len(re.findall(r'\bdef\s+\w+', code))
                analysis['classes'] = len(re.findall(r'\bclass\s+\w+', code))
                analysis['imports'] = len(re.findall(r'^(?:import|from)\s+', code, re.M))
                analysis['comments'] = len(re.findall(r'#.*$', code, re.M))
                
            return {
                'success': True,
                **analysis
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _debug_code(self, code: str, error: str) -> Dict[str, Any]:
        """Debug code based on error"""
        # Simple heuristics for common errors
        suggestions = []
        
        if 'SyntaxError' in error:
            suggestions.append('Check for missing colons, brackets, or quotes')
        if 'NameError' in error:
            suggestions.append('Check variable names - may be undefined')
        if 'IndexError' in error:
            suggestions.append('Check list/array bounds')
        if 'TypeError' in error:
            suggestions.append('Check function arguments and types')
        if 'ImportError' in error:
            suggestions.append('Check module name and installation')
            
        return {
            'success': True,
            'error_type': error.split(':')[0] if ':' in error else 'Unknown',
            'suggestions': suggestions,
            'error': error
        }
        
    # ==================== SYSTEM TOOLS ====================
    
    async def _system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import psutil
            
            return {
                'success': True,
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                },
                'boot_time': psutil.boot_time()
            }
            
        except ImportError:
            return {
                'success': True,
                'error': 'psutil not available'
            }
            
    async def _execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'Command timeout', 'success': False}
        except Exception as e:
            return {'error': str(e), 'success': False}
            
    async def _manage_process(self, action: str, pid: Optional[int] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """Manage system processes"""
        try:
            import psutil
            
            if action == 'list':
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    processes.append(proc.info)
                return {'success': True, 'processes': processes[:20]}
                
            elif action == 'kill' and pid:
                process = psutil.Process(pid)
                process.terminate()
                return {'success': True, 'message': f'Process {pid} terminated'}
                
            elif action == 'find' and name:
                matches = []
                for proc in psutil.process_iter(['pid', 'name']):
                    if name.lower() in proc.info['name'].lower():
                        matches.append(proc.info)
                return {'success': True, 'matches': matches}
                
            return {'error': 'Invalid action or missing parameters'}
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _control_apps(self, action: str, app_name: str) -> Dict[str, Any]:
        """Control applications"""
        # Platform-specific implementation
        import sys
        
        try:
            if sys.platform == 'win32':
                if action == 'open':
                    subprocess.Popen(['start', app_name], shell=True)
                    return {'success': True, 'message': f'Opened {app_name}'}
                elif action == 'close':
                    subprocess.run(['taskkill', '/f', '/im', app_name], capture_output=True)
                    return {'success': True, 'message': f'Closed {app_name}'}
            else:
                if action == 'open':
                    subprocess.Popen([app_name])
                    return {'success': True, 'message': f'Opened {app_name}'}
                    
            return {'error': 'Unsupported action or platform'}
            
        except Exception as e:
            return {'error': str(e)}
            
    # ==================== WEB TOOLS ====================
    
    async def _web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search the web"""
        # Placeholder - would integrate with search API
        return {
            'success': True,
            'query': query,
            'results': [
                {'title': f'Result for "{query[:30]}..."', 'url': 'https://example.com/1'},
                {'title': 'Another result', 'url': 'https://example.com/2'}
            ],
            'note': 'Web search requires API integration (e.g., SerpAPI, Google Custom Search)'
        }
        
    async def _fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch URL content"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    content = await response.text()
                    
                    # Limit content size
                    if len(content) > 100000:
                        content = content[:100000] + '... [truncated]'
                        
                    return {
                        'success': True,
                        'url': url,
                        'status': response.status,
                        'content': content,
                        'size': len(content)
                    }
                    
        except ImportError:
            return {'error': 'aiohttp not installed'}
        except Exception as e:
            return {'error': str(e)}
            
    # ==================== DATA TOOLS ====================
    
    async def _analyze_csv(self, path: str) -> Dict[str, Any]:
        """Analyze CSV file"""
        try:
            import csv
            
            file_path = Path(path).expanduser()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if not rows:
                return {'error': 'Empty CSV file'}
                
            # Basic analysis
            columns = list(rows[0].keys())
            analysis = {
                'rows': len(rows),
                'columns': len(columns),
                'column_names': columns,
                'sample': rows[:3]
            }
            
            # Numeric column stats
            for col in columns:
                try:
                    values = [float(r[col]) for r in rows if r[col]]
                    if values:
                        analysis[f'{col}_stats'] = {
                            'min': min(values),
                            'max': max(values),
                            'avg': sum(values) / len(values)
                        }
                except:
                    pass
                    
            return {
                'success': True,
                'path': str(file_path),
                **analysis
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def _create_chart(self, data: List, chart_type: str = 'bar') -> Dict[str, Any]:
        """Create chart from data"""
        # Placeholder - would generate actual chart
        return {
            'success': True,
            'chart_type': chart_type,
            'data_points': len(data),
            'note': 'Chart generation requires matplotlib/plotly integration'
        }
        
    async def _extract_data(self, text: str, pattern: str) -> Dict[str, Any]:
        """Extract data using pattern"""
        try:
            matches = re.findall(pattern, text)
            return {
                'success': True,
                'pattern': pattern,
                'matches': matches,
                'count': len(matches)
            }
        except Exception as e:
            return {'error': str(e)}
            
    async def _compare_data(self, data1: Any, data2: Any) -> Dict[str, Any]:
        """Compare two datasets"""
        try:
            return {
                'success': True,
                'same_type': type(data1) == type(data2),
                'size_1': len(data1) if hasattr(data1, '__len__') else 'N/A',
                'size_2': len(data2) if hasattr(data2, '__len__') else 'N/A',
                'diff': 'Comparison requires structured data'
            }
        except Exception as e:
            return {'error': str(e)}
            
    # ==================== TOOL ACCESS ====================
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get tool by name"""
        return self.tools.get(name)
        
    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())
        
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute tool by name"""
        tool = self.tools.get(name)
        if not tool:
            return {'error': f'Tool not found: {name}'}
            
        try:
            return await tool(**kwargs)
        except Exception as e:
            return {'error': str(e)}
