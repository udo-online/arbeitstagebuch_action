import importlib

modules = [
    "flask",
    "reportlab",
    "pydrive2",
    "googleapiclient",
    "google.auth",
    "google_auth_oauthlib",
    "google_auth_httplib2",
]

print("🔍 Prüfe installierte Module...\n")

for module in modules:
    try:
        importlib.import_module(module)
        print(f"✅ {module} gefunden")
    except ImportError:
        print(f"❌ {module} NICHT installiert")

print("\nFertig ✅")
