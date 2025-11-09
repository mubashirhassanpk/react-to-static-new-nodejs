"""
Project Type Detector for Static Site Builder
Detects and configures various frontend frameworks for static builds
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ProjectType:
    """Project type constants"""
    CREATE_REACT_APP = "create-react-app"
    VITE_REACT = "vite-react"
    VITE_SVELTE = "vite-svelte"
    VITE_VUE = "vite-vue"
    VITE_GENERIC = "vite"
    NEXTJS = "nextjs"
    VUE_CLI = "vue-cli"
    NUXT = "nuxt"
    SVELTEKIT = "sveltekit"
    ANGULAR = "angular"
    GENERIC_NODEJS = "nodejs"
    UNKNOWN = "unknown"


class ProjectDetector:
    """Detects project type and provides build configuration"""
    
    @staticmethod
    def detect_project_type(project_dir: Path) -> Tuple[str, Dict]:
        """
        Detect the project type from package.json
        
        Returns:
            Tuple of (project_type, build_info)
            build_info contains: {
                'build_command': str,
                'output_dirs': List[str],  # Priority order
                'requires_config': bool,
                'framework_name': str
            }
        """
        package_json_path = project_dir / "package.json"
        
        if not package_json_path.exists():
            return ProjectType.UNKNOWN, {
                'build_command': None,
                'output_dirs': [],
                'requires_config': False,
                'framework_name': 'Unknown',
                'error': 'No package.json found'
            }
        
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse package.json: {e}")
            return ProjectType.UNKNOWN, {
                'build_command': None,
                'output_dirs': [],
                'requires_config': False,
                'framework_name': 'Unknown',
                'error': f'Invalid package.json: {str(e)}'
            }
        
        deps = package_data.get('dependencies', {})
        dev_deps = package_data.get('devDependencies', {})
        all_deps = {**deps, **dev_deps}
        scripts = package_data.get('scripts', {})
        
        # Next.js Detection
        if 'next' in all_deps:
            return ProjectType.NEXTJS, {
                'build_command': 'next build',
                'output_dirs': ['out', '.next'],  # out for static export, .next as fallback
                'requires_config': True,
                'framework_name': 'Next.js',
                'config_files': ['next.config.js', 'next.config.mjs', 'next.config.ts']
            }
        
        # Nuxt Detection
        if 'nuxt' in all_deps or 'nuxt3' in all_deps:
            return ProjectType.NUXT, {
                'build_command': 'nuxt generate' if 'generate' in scripts else 'nuxt build',
                'output_dirs': ['.output/public', 'dist', '.nuxt/dist'],
                'requires_config': True,
                'framework_name': 'Nuxt.js',
                'config_files': ['nuxt.config.js', 'nuxt.config.ts']
            }
        
        # SvelteKit Detection
        if '@sveltejs/kit' in all_deps:
            return ProjectType.SVELTEKIT, {
                'build_command': 'vite build' if 'build' in scripts else 'svelte-kit build',
                'output_dirs': ['build', '.svelte-kit/output'],
                'requires_config': True,
                'framework_name': 'SvelteKit',
                'config_files': ['svelte.config.js']
            }
        
        # Angular Detection
        if '@angular/core' in all_deps:
            project_name = package_data.get('name', 'app')
            return ProjectType.ANGULAR, {
                'build_command': 'ng build --configuration production' if 'ng' in scripts else 'npm run build',
                'output_dirs': [f'dist/{project_name}/browser', f'dist/{project_name}', 'dist'],
                'requires_config': False,
                'framework_name': 'Angular',
                'project_name': project_name
            }
        
        # Create React App Detection
        if 'react-scripts' in all_deps:
            return ProjectType.CREATE_REACT_APP, {
                'build_command': 'react-scripts build',
                'output_dirs': ['build'],
                'requires_config': False,
                'framework_name': 'Create React App'
            }
        
        # Vue CLI Detection
        if '@vue/cli-service' in all_deps:
            return ProjectType.VUE_CLI, {
                'build_command': 'vue-cli-service build',
                'output_dirs': ['dist'],
                'requires_config': False,
                'framework_name': 'Vue CLI'
            }
        
        # Vite Detection (check what framework it's using)
        if 'vite' in all_deps:
            if 'react' in all_deps or 'react-dom' in all_deps:
                framework = 'Vite + React'
                project_type = ProjectType.VITE_REACT
            elif 'svelte' in all_deps:
                framework = 'Vite + Svelte'
                project_type = ProjectType.VITE_SVELTE
            elif 'vue' in all_deps:
                framework = 'Vite + Vue'
                project_type = ProjectType.VITE_VUE
            else:
                framework = 'Vite'
                project_type = ProjectType.VITE_GENERIC
            
            return project_type, {
                'build_command': 'vite build',
                'output_dirs': ['dist'],
                'requires_config': False,
                'framework_name': framework
            }
        
        # Generic Node.js with build script
        if 'build' in scripts:
            return ProjectType.GENERIC_NODEJS, {
                'build_command': scripts['build'],
                'output_dirs': ['dist', 'build', 'out', 'public'],
                'requires_config': False,
                'framework_name': 'Node.js'
            }
        
        # No build script found
        return ProjectType.UNKNOWN, {
            'build_command': None,
            'output_dirs': [],
            'requires_config': False,
            'framework_name': 'Unknown',
            'error': 'No build script found in package.json'
        }
    
    @staticmethod
    def configure_nextjs_static_export(project_dir: Path) -> Tuple[bool, str]:
        """
        Configure Next.js for static export by adding output: 'export'
        Supports both .js and .mjs config files
        
        Returns:
            Tuple of (success, message)
        """
        config_files = ['next.config.js', 'next.config.mjs', 'next.config.ts']
        config_path = None
        
        for config_file in config_files:
            path = project_dir / config_file
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            # Create a new next.config.js
            config_path = project_dir / 'next.config.js'
            try:
                config_content = """/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
"""
                config_path.write_text(config_content, encoding='utf-8')
                return True, "Created next.config.js with static export configuration"
            except Exception as e:
                return False, f"Failed to create next.config.js: {str(e)}"
        
        # Read existing config
        try:
            content = config_path.read_text(encoding='utf-8')
            
            # Check if output: 'export' already exists
            if re.search(r"output\s*:\s*['\"]export['\"]", content):
                return True, "Next.js already configured for static export"
            
            # Determine if it's ES modules or CommonJS
            is_esm = config_path.suffix == '.mjs' or 'export default' in content
            
            if is_esm:
                # Handle ES modules syntax
                if 'export default' in content:
                    # Add output: 'export' to existing config object
                    content = re.sub(
                        r'(export\s+default\s+\{)',
                        r"\1\n  output: 'export',\n  images: { unoptimized: true },",
                        content,
                        count=1
                    )
                else:
                    # Create new export
                    content += "\n\nexport default {\n  output: 'export',\n  images: { unoptimized: true },\n}\n"
            else:
                # Handle CommonJS syntax
                if 'module.exports' in content:
                    # Add to existing exports
                    content = re.sub(
                        r'(module\.exports\s*=\s*\{)',
                        r"\1\n  output: 'export',\n  images: { unoptimized: true },",
                        content,
                        count=1
                    )
                else:
                    # Create new exports
                    content += "\n\nmodule.exports = {\n  output: 'export',\n  images: { unoptimized: true },\n}\n"
            
            # Write back the modified config
            config_path.write_text(content, encoding='utf-8')
            return True, f"Modified {config_path.name} to enable static export"
            
        except Exception as e:
            return False, f"Failed to modify {config_path.name}: {str(e)}"
    
    @staticmethod
    def configure_nuxt_static_generation(project_dir: Path) -> Tuple[bool, str]:
        """
        Configure Nuxt for static generation
        
        Returns:
            Tuple of (success, message)
        """
        config_files = ['nuxt.config.js', 'nuxt.config.ts']
        config_path = None
        
        for config_file in config_files:
            path = project_dir / config_file
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            # Create a new nuxt.config.js for static generation
            config_path = project_dir / 'nuxt.config.js'
            try:
                config_content = """export default {
  ssr: false,
  target: 'static',
}
"""
                config_path.write_text(config_content, encoding='utf-8')
                return True, "Created nuxt.config.js with static generation configuration"
            except Exception as e:
                return False, f"Failed to create nuxt.config.js: {str(e)}"
        
        try:
            content = config_path.read_text(encoding='utf-8')
            
            # Check if already configured for static
            if 'target' in content and 'static' in content:
                return True, "Nuxt already configured for static generation"
            
            # Add static target configuration
            if 'export default' in content:
                content = re.sub(
                    r'(export\s+default\s+\{)',
                    r"\1\n  ssr: false,\n  target: 'static',",
                    content,
                    count=1
                )
            else:
                content += "\n\nexport default {\n  ssr: false,\n  target: 'static',\n}\n"
            
            config_path.write_text(content, encoding='utf-8')
            return True, f"Modified {config_path.name} for static generation"
            
        except Exception as e:
            return False, f"Failed to modify {config_path.name}: {str(e)}"
    
    @staticmethod
    def find_build_output(project_dir: Path, possible_dirs: List[str]) -> Optional[Path]:
        """
        Find the actual build output directory from a list of possibilities
        
        Args:
            project_dir: The project root directory
            possible_dirs: List of possible output directory paths (in priority order)
        
        Returns:
            Path to the build output directory, or None if not found
        """
        for dir_name in possible_dirs:
            output_path = project_dir / dir_name
            if output_path.exists() and output_path.is_dir():
                # Check if directory has content (not empty)
                if any(output_path.iterdir()):
                    logger.info(f"Found build output at: {output_path}")
                    return output_path
        
        return None
