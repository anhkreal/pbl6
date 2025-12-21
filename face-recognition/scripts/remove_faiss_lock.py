"""
Script to remove unnecessary faiss_lock usage from all service files.
FaissIndexManager already has internal RLock, so external lock is redundant.

Run this script to automatically refactor all service files.
"""

import os
import re

# Service files that use faiss_lock
SERVICE_DIR = "service"

def remove_faiss_lock_from_file(filepath):
    """Remove faiss_lock import and usage from a service file."""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # 1. Remove faiss_lock from import
    if 'get_faiss_lock' in content:
        content = re.sub(
            r'from service\.shared_instances import ([^)]+)get_faiss_lock,?\s*',
            r'from service.shared_instances import \1',
            content
        )
        content = re.sub(
            r',\s*get_faiss_lock',
            '',
            content
        )
        changes_made.append("Removed get_faiss_lock from imports")
    
    # 2. Remove faiss_lock = get_faiss_lock() assignment
    if 'faiss_lock = get_faiss_lock()' in content:
        content = re.sub(
            r'\nfaiss_lock = get_faiss_lock\(\)\s*\n',
            '\n',
            content
        )
        changes_made.append("Removed faiss_lock assignment")
    
    # 3. Remove 'with faiss_lock:' blocks but keep indented content
    # This is tricky - need to dedent the content inside
    def dedent_block(match):
        """Dedent the content inside with faiss_lock: block"""
        indentation = match.group(1)
        content_lines = match.group(2).split('\n')
        
        # Dedent each line by 4 spaces (1 indentation level)
        dedented_lines = []
        for line in content_lines:
            if line.startswith('    '):
                dedented_lines.append(line[4:])
            else:
                dedented_lines.append(line)
        
        # Add comment about thread-safety
        comment = f"{indentation}# Thread-safe: FaissIndexManager has internal RLock\n"
        return comment + '\n'.join(dedented_lines)
    
    # Pattern to match 'with faiss_lock:' and its indented block
    pattern = r'(\s*)with faiss_lock:\s*\n((?:\1    .+\n?)*)'
    
    if 'with faiss_lock:' in content:
        content = re.sub(pattern, dedent_block, content)
        changes_made.append("Removed 'with faiss_lock:' blocks")
    
    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, changes_made
    
    return False, []


def main():
    """Process all service files."""
    
    if not os.path.exists(SERVICE_DIR):
        print(f"❌ Service directory not found: {SERVICE_DIR}")
        return
    
    print("🔍 Scanning service files for faiss_lock usage...\n")
    
    total_files = 0
    modified_files = 0
    
    for filename in os.listdir(SERVICE_DIR):
        if filename.endswith('.py') and filename != '__pycache__':
            filepath = os.path.join(SERVICE_DIR, filename)
            total_files += 1
            
            modified, changes = remove_faiss_lock_from_file(filepath)
            
            if modified:
                modified_files += 1
                print(f"✅ Modified: {filename}")
                for change in changes:
                    print(f"   - {change}")
                print()
    
    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   Total files scanned: {total_files}")
    print(f"   Files modified: {modified_files}")
    print(f"   Files unchanged: {total_files - modified_files}")
    print(f"{'='*60}")
    
    if modified_files > 0:
        print("\n✅ Refactoring complete!")
        print("⚠️  Please test the application to ensure everything works.")
        print("💡 Run: python test_thread_safety.py")
    else:
        print("\n✅ No files need modification - all good!")


if __name__ == '__main__':
    main()
