"""Thin example wrapper — prefer: python -m genelytics.demo"""

from genelytics.demo import create_app, main

__all__ = ["create_app", "main"]

if __name__ == "__main__":
    main()
