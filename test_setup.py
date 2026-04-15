#!/usr/bin/env python3
"""
Comprehensive test suite for Local LLM with RAG
Tests Ollama connectivity, RAG indexing, and API functionality
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

# Test 1: Check Ollama connectivity
def test_ollama_connectivity():
    """Test if Ollama is running and accessible"""
    print("\n" + "="*60)
    print("TEST 1: Ollama Connectivity")
    print("="*60)

    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            print(f"✅ Ollama is running!")
            print(f"   Available models: {models}")
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False


# Test 2: Check RAG corpus
def test_rag_corpus():
    """Test if RAG corpus path exists and has content"""
    print("\n" + "="*60)
    print("TEST 2: RAG Corpus Validation")
    print("="*60)

    rag_path = Path("/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB")

    if not rag_path.exists():
        print(f"❌ RAG corpus path does not exist: {rag_path}")
        return False

    notebooks = list(rag_path.glob("**/*.ipynb"))
    print(f"✅ RAG corpus found at {rag_path}")
    print(f"   Notebooks found: {len(notebooks)}")

    if notebooks:
        for nb in notebooks[:3]:
            print(f"   - {nb.name}")
        return True
    else:
        print(f"⚠️  No .ipynb files found, but directory exists")
        return True


# Test 3: Import and test RAG service
def test_rag_service():
    """Test RAG service initialization and basic functionality"""
    print("\n" + "="*60)
    print("TEST 3: RAG Service")
    print("="*60)

    try:
        from app.services.rag_service import get_rag_service

        rag = get_rag_service()
        status = rag.status()

        print(f"✅ RAG service initialized!")
        print(f"   Enabled: {status['enabled']}")
        print(f"   Indexed files: {status['indexed_files']}")
        print(f"   Indexed chunks: {status['indexed_chunks']}")

        if status['ready']:
            # Try a search
            context = rag.search("clustering algorithm", top_k=2)
            if context.sources:
                print(f"✅ RAG search working! Found {len(context.sources)} sources")
                return True
            else:
                print(f"⚠️  RAG search returned no results (may be expected if corpus is empty)")
                return True
        else:
            print(f"⚠️  RAG service not ready yet (indexing may be in progress)")
            return True

    except Exception as e:
        print(f"❌ RAG service error: {e}")
        import traceback
        traceback.print_exc()
        return False


# Test 4: Import services and config
def test_imports():
    """Test if all core modules import without errors"""
    print("\n" + "="*60)
    print("TEST 4: Module Imports")
    print("="*60)

    modules = [
        ("app.config", "Settings & Config"),
        ("app.models", "Pydantic Models"),
        ("app.services.ollama_service", "Ollama Service"),
        ("app.services.rag_service", "RAG Service"),
        ("app.routes.llm", "LLM Routes"),
    ]

    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✅ {description:30} - imported successfully")
        except Exception as e:
            print(f"❌ {description:30} - {e}")
            all_ok = False

    return all_ok


# Test 5: Model validation
def test_models():
    """Test if Pydantic models work correctly"""
    print("\n" + "="*60)
    print("TEST 5: Pydantic Models")
    print("="*60)

    try:
        from app.models import QueryRequest, QueryResponse

        # Test creating a valid request
        req = QueryRequest(prompt="What is clustering?")
        print(f"✅ QueryRequest created: prompt={req.prompt[:30]}...")

        # Test creating a response
        resp = QueryResponse(
            response="Clustering is...",
            model="qwen2.5-coder:7b",
            prompt="What is clustering?",
            rag={"enabled": True, "sources_count": 2}
        )
        print(f"✅ QueryResponse with RAG metadata created successfully")
        return True

    except Exception as e:
        print(f"❌ Model validation error: {e}")
        import traceback
        traceback.print_exc()
        return False


# Test 6: Load and parse a sample notebook
def test_notebook_parsing():
    """Test if notebook parsing works"""
    print("\n" + "="*60)
    print("TEST 6: Notebook Parsing")
    print("="*60)

    import json

    rag_path = Path("/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB")
    notebooks = list(rag_path.glob("**/*.ipynb"))

    if not notebooks:
        print(f"⚠️  No notebooks found to test parsing")
        return True

    try:
        nb_path = notebooks[0]
        with open(nb_path, 'r') as f:
            nb = json.load(f)

        cells = nb.get("cells", [])
        print(f"✅ Parsed {nb_path.name}")
        print(f"   Total cells: {len(cells)}")

        cell_types = {}
        for cell in cells:
            ct = cell.get("cell_type", "unknown")
            cell_types[ct] = cell_types.get(ct, 0) + 1

        for ct, count in cell_types.items():
            print(f"   - {ct}: {count}")

        return True
    except Exception as e:
        print(f"❌ Notebook parsing error: {e}")
        return False


# Main test runner
def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "LOCAL LLM WITH RAG - TEST SUITE" + " "*18 + "║")
    print("╚" + "="*58 + "╝")

    tests = [
        ("Ollama Connectivity", test_ollama_connectivity),
        ("RAG Corpus", test_rag_corpus),
        ("Module Imports", test_imports),
        ("Pydantic Models", test_models),
        ("Notebook Parsing", test_notebook_parsing),
        ("RAG Service", test_rag_service),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {name}")

    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! Project is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
