#!/usr/bin/env python3
"""
Create missing directories as per CLEANUP_PLAN.md
"""

import os

def create_directories():
    """Create the missing directories for better code organization"""
    
    directories = [
        'src/evaluation',
        'src/utils', 
        'notebooks',
        'docs',
        'tests',
        'scripts/diagnostics'
    ]
    
    print("Creating missing directories...")
    print("=" * 50)
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created: {directory}")
            
            # Add __init__.py to Python packages
            if directory.startswith('src/') or directory == 'tests':
                init_file = os.path.join(directory, '__init__.py')
                with open(init_file, 'w') as f:
                    f.write('"""Package initialization"""')
                print(f"   Added __init__.py to {directory}")
        else:
            print(f"⏭️  Already exists: {directory}")
    
    # Create a .gitkeep in notebooks to ensure it's tracked
    gitkeep_path = 'notebooks/.gitkeep'
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, 'w') as f:
            f.write('')
        print(f"✅ Created: {gitkeep_path}")
    
    print("\n✨ Directory structure setup complete!")
    print("\nNext steps:")
    print("1. Move diagnostic scripts to scripts/diagnostics/")
    print("2. Move utility functions to src/utils/")
    print("3. Create evaluation scripts in src/evaluation/")

if __name__ == "__main__":
    create_directories()
