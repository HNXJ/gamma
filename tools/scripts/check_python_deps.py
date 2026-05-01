REQUIRED = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "httpx",
    "requests",
    "numpy",
    "scipy",
    "pandas",
    "jax",
    "chex",
]

failed = []
for name in REQUIRED:
    try:
        __import__(name)
    except Exception as e:
        failed.append(f"{name}: {e}")

if failed:
    print("DEPENDENCY_CHECK_FAILED")
    for item in failed:
        print(item)
    raise SystemExit(1)

print("DEPENDENCY_CHECK_OK")
