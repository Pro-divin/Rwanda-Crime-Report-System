#!/usr/bin/env python
"""
Setup script for Rwanda Report System
Initializes database migrations and creates necessary directories
"""

import os
import sys
import django
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command

def setup_project():
    """Initialize project database and create directories"""
    
    print("🚀 Rwanda Report System - Setup Script")
    print("=" * 50)
    
    # Create media directories
    media_root = backend_path / 'media'
    media_root.mkdir(exist_ok=True)
    (media_root / 'reports').mkdir(exist_ok=True)
    (media_root / 'reports' / 'media').mkdir(exist_ok=True)
    (media_root / 'reports' / 'thumbnails').mkdir(exist_ok=True)
    print("✅ Media directories created")
    
    # Run migrations
    print("\n📦 Running database migrations...")
    call_command('makemigrations', 'users')
    call_command('makemigrations', 'reports')
    call_command('makemigrations', 'blockchain')
    print("✅ Migrations created")
    
    call_command('migrate')
    print("✅ Database migrated")
    
    # Create superuser
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        print("\n👤 Creating superuser...")
        User.objects.create_superuser('admin', 'admin@rrs.rw', 'admin123')
        print("✅ Superuser created: admin / admin123")
    else:
        print("✅ Superuser already exists")
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\n🎯 Next steps:")
    print("  1. Start Django: python manage.py runserver")
    print("  2. Access admin: http://localhost:8000/admin/")
    print("  3. Submit reports: http://localhost:8000/report/submit/")
    print("  4. Check status: http://localhost:8000/report/status/")
    print("\n" + "=" * 50)

if __name__ == '__main__':
    setup_project()
