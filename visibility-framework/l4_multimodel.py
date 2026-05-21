"""
L4 Multi-Model Polling — Industry Standard Setup.
4 models, 20 prompts × 3 repeats = 60 queries per model = 240 total per audit.
"""
import os

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

MODELS = {
    "chatgpt-4o":       {"provider": "openai",    "model": "gpt-4o",          "key": OPENAI_KEY,   "active": bool(OPENAI_KEY)},
    "chatgpt-mini":     {"provider": "openai",    "model": "gpt-4.1-mini",    "key": OPENAI_KEY,   "active": bool(OPENAI_KEY)},
    "claude-sonnet":    {"provider": "anthropic", "model": "claude-sonnet-4-6","key": ANTHROPIC_KEY,"active": bool(ANTHROPIC_KEY)},
    "claude-haiku":     {"provider": "anthropic", "model": "claude-haiku-4-5", "key": ANTHROPIC_KEY,"active": bool(ANTHROPIC_KEY)},
    "perplexity-sonar": {"provider": "perplexity","model": "sonar",           "key": "",           "active": False},
    "gemini-flash":     {"provider": "google",    "model": "gemini-2.5-flash", "key": "",          "active": False},
    "copilot":          {"provider": "openai",    "model": "gpt-4o",          "key": OPENAI_KEY,   "active": False},  # uses same API, different prompt framing
}

# Industry standard: segmented by funnel stage, buyer language
PROMPTS = {
    "discovery": [
        # Core should-cost (primary product)
        "should cost modeling software for procurement teams",
        "how to estimate what a product should cost to manufacture",
        "replace spreadsheet cost estimation with software",
        "AI should-cost analysis for product OEMs",
        "tools to break down BOM costs before supplier negotiations",
        "how procurement teams estimate material labor and overhead costs",
        "software to generate cost models without supplier quotes",
        "what is should cost analysis for manufactured products",
        "how do cost engineers build should cost models",
        # Industry-specific (matches segments A, B, C)
        "should cost software for consumer hard goods manufacturers",
        "cost estimation tools for industrial equipment companies",
        "product cost modeling for mid-market manufacturers",
        "how appliance manufacturers estimate production costs",
        "cost engineering software for complex BOM products",
        # Secondary features (tariff + PCF)
        "tariff impact analysis software for importers",
        "how to model tariff costs on imported components",
        "CBAM compliance software for manufacturers exporting to Europe",
        "product carbon footprint software for product OEMs",
        "how to calculate PCF without supplier data",
    ],
    "evaluation": [
        "should cost software comparison",
        "apriori alternatives for cost estimation",
        "apriori vs spreadsheet cost modeling",
        "galorath alternatives for manufacturers",
        "best should cost analysis platforms",
        "cost estimation software for procurement professionals",
        "tool to replace Excel for product cost estimation",
        "AI vs traditional should cost modeling",
    ],
    "decision": [
        "{brand} alternatives for should cost modeling",
        "{brand} vs apriori for cost estimation",
        "{brand} reviews from procurement teams",
        "is {brand} good for should cost analysis",
        "what companies use {brand} for cost modeling",
        "companies using {brand} for product cost estimation",
        "should cost software with tariff modeling capabilities",
        "software that does both should cost and carbon footprint",
        "{brand} customer reviews",
    ],
}

def build_prompts(brand: str) -> list:
    all_prompts = PROMPTS["discovery"] + PROMPTS["evaluation"]
    all_prompts += [p.format(brand=brand) for p in PROMPTS["decision"]]
    return all_prompts * 3  # 20 × 3 = 60


def patch_for_multimodel():
    """Monkey-patch auditstack for multi-model L4 polling."""
    import auditstack.stages.ai_retrieval as _ai_mod
    from auditstack.llm.providers.openai import OpenAIProvider
    from auditstack.llm.providers.anthropic import AnthropicProvider
    from auditstack.llm.providers.base import CostTier

    # Per-model provider classes
    class GPT4oProvider(OpenAIProvider):
        name = "chatgpt-4o"
        def __init__(self): super().__init__(); self.default_model = "gpt-4o"

    class GPTMiniProvider(OpenAIProvider):
        name = "chatgpt-mini"
        def __init__(self): super().__init__(); self.default_model = "gpt-4.1-mini"

    class ClaudeSonnetProvider(AnthropicProvider):
        name = "claude-sonnet"
        def __init__(self): super().__init__(); self.default_model = "claude-sonnet-4-6"

    class ClaudeHaikuProvider(AnthropicProvider):
        name = "claude-haiku"
        def __init__(self): super().__init__(); self.default_model = "claude-haiku-4-5"

    # Patch router
    import auditstack.llm.router as _router_mod
    _orig_dr = _router_mod.default_router
    def patched_router():
        r = _orig_dr()
        polling = []
        if OPENAI_KEY:
            polling.extend([GPT4oProvider(), GPTMiniProvider()])
        if ANTHROPIC_KEY:
            polling.extend([ClaudeSonnetProvider(), ClaudeHaikuProvider()])
        if polling:
            r.providers_by_tier[CostTier.POLLING] = polling
        return r
    _router_mod.default_router = patched_router

    # Patch platforms (only active models)
    _ai_mod.POLLING_PLATFORMS = [name for name, cfg in MODELS.items() if cfg["active"]]

    _orig_run = _ai_mod.AIRetrievalStage.run
    def patched_run(self, snapshot, ctx):
        brand = ctx.client_name or "Muir AI"
        self._prompts = build_prompts(brand)
        return _orig_run(self, snapshot, ctx)
    _ai_mod.AIRetrievalStage.run = patched_run

    # Patch polling to run in parallel (ThreadPoolExecutor)
    import concurrent.futures
    from auditstack.llm.router import LLMRouter
    _orig_classify = _ai_mod._classify_response

    def _poll_parallel(router: LLMRouter, prompts: list, brand: str, competitors: list, max_workers: int = 8):
        """Run all prompts in parallel through the polling tier."""
        results = []
        def _poll_one(prompt):
            try:
                result = router.complete(
                    system="You are a helpful assistant. Answer directly.",
                    user=prompt, tier=CostTier.POLLING, stage_name="ai_retrieval", max_tokens=600)
                classification = _orig_classify(result.text, brand, competitors)
                return {"prompt": prompt, "text": result.text[:300],
                        "mentioned": classification["client_mentioned"],
                        "competitors": classification["competitors_mentioned"],
                        "cost": result.cost_usd}
            except Exception as e:
                return {"prompt": prompt, "error": str(e), "mentioned": False, "competitors": [], "cost": 0.0}

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(_poll_one, p) for p in prompts]
            for fut in concurrent.futures.as_completed(futures):
                results.append(fut.result())
        return results

    # Store parallel poll function on the module for the patched run to use
    _ai_mod._poll_parallel = _poll_parallel
