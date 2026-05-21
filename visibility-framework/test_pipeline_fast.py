"""Fast test of ContentV2 + Layer3 pipeline. 3 pages, no heavy layers."""
import importlib.util, sys, json, time, os

# Load our stages
for name, fpath in [("content_stage_v2", "context/knowledge/visibility-framework/content_stage_v2.py"),
                      ("layer3_stage", "context/knowledge/visibility-framework/layer3_stage.py")]:
    spec = importlib.util.spec_from_file_location(name, fpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)

from auditstack.context import AuditContext, ClientType
from auditstack.orchestrator import Pipeline
from auditstack.registry import REGISTRY
from auditstack.cli import _register_bundled_stages

os.environ["DEEPSEEK_KEY"] = "sk-0d31b1d5c7a64b48ac945e5991578e2e"

# Register only what we need: technical + content_v2 + external_presence
_register_bundled_stages()
REGISTRY.unregister("content")
REGISTRY.unregister("entity")
REGISTRY.unregister("platform_mix")
REGISTRY.unregister("indexability")
REGISTRY.unregister("ai_retrieval")
REGISTRY.unregister("anomaly")
REGISTRY.unregister("render")

from content_stage_v2 import ContentStageV2
from layer3_stage import ExternalPresenceStage
REGISTRY.register(ContentStageV2(max_pages=3))
REGISTRY.register(ExternalPresenceStage())

ctx = AuditContext(
    target_url="https://www.muir.ai",
    client_name="Muir AI",
    client_description="Manufacturing cost estimation platform",
    client_type=ClientType.B2B_SAAS,
    competitors=["https://www.apriori.com", "https://galorath.com"],
)

print("Running: technical → content_v2 → external_presence\n")
t0 = time.time()
pipeline = Pipeline()
result = pipeline.run(ctx)
elapsed = time.time() - t0

# Show results
snap = result.snapshot
print(f"\nDone in {elapsed:.0f}s")
print(f"State: {snap.state}")
print(f"Composite: {snap.composite_score}")
print(f"Layer scores: {snap.layer_scores}")

for stage_name in ["technical", "content", "external_presence"]:
    stage = snap.stages.get(stage_name)
    if stage and stage.output:
        out = stage.output
        print(f"\n[{stage_name}] score={out.get('layer_score')}")
        if stage_name == "content":
            print(f"  Pages: {out.get('pages_analyzed')}, Citability: {out.get('avg_citability')}, Flesch: {out.get('avg_flesch')}")
        elif stage_name == "external_presence":
            plats = out.get("platforms", {})
            for pname, pdata in plats.items():
                print(f"  {pname}: {pdata.get('score','?')}/10")
