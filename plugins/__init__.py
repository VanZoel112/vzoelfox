# plugins/__init__.py
"""
VZoeluBot Plugins Package
"""

try:
    from .vzoel_assistant import assistant_handler
    from .vzoel_complete import complete_handler
    
    # Export all handlers
    __all__ = [
        'assistant_handler',
        'complete_handler'
    ]
    
    print("✅ VZoeluBot plugins loaded successfully!")
    print(f"  - VZoel Assistant: {assistant_handler['version']}")
    print(f"  - VZoel Complete: {complete_handler['version']}")
    
except ImportError as e:
    print(f"❌ Plugin import error: {e}")
    __all__ = []
