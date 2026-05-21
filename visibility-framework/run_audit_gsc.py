"""Run auditstack with Google Search Console OAuth.

Usage:
    python run_audit_gsc.py https://www.muir.ai \
        --client-name "Muir AI" \
        --client-description "Manufacturing cost estimation platform" \
        --competitors "https://www.apriori.com,https://galorath.com" \
        --client-type b2b_saas \
        --secret-file /path/to/client_secret.json
"""

import argparse
import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

from auditstack.context import AuditContext, GoogleOAuthScopes, ClientType
from auditstack.orchestrator import Pipeline
from auditstack.registry import REGISTRY


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_google_token(secret_file: str, token_cache: str = "gsc_token.pickle") -> str:
    """Run OAuth flow and return an access token. Caches refresh token locally."""
    creds = None

    if os.path.exists(token_cache):
        with open(token_cache, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_cache, "wb") as f:
            pickle.dump(creds, f)

    creds.refresh(Request())
    return creds.token


def main():
    parser = argparse.ArgumentParser(description="Run auditstack with GSC OAuth")
    parser.add_argument("url", help="Target URL to audit")
    parser.add_argument("--client-name", default=None)
    parser.add_argument("--client-description", default=None)
    parser.add_argument("--competitors", default="", help="Comma-separated competitor URLs")
    parser.add_argument("--client-type", default="unknown",
                        choices=["b2b_saas", "b2b_services", "dtc", "consumer", "unknown"])
    parser.add_argument("--output-dir", default="./audits")
    parser.add_argument("--secret-file", required=True,
                        help="Path to Google OAuth client_secret.json")
    args = parser.parse_args()

    # Run OAuth to get access token
    print("Authenticating with Google...")
    access_token = get_google_token(args.secret_file)
    print("Got access token.")

    # Build Google OAuth scopes with the token
    google_oauth = GoogleOAuthScopes(
        gsc=True,
        access_token=access_token,
    )

    # Parse client type
    client_type = ClientType[args.client_type.upper()]

    # Parse competitors
    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]

    # Build context
    ctx = AuditContext(
        target_url=args.url,
        client_name=args.client_name,
        client_description=args.client_description,
        client_type=client_type,
        competitors=competitors,
        google_oauth=google_oauth,
        persistence_root=args.output_dir,
    )

    # Register stages — use our ContentStageV2 instead of bundled
    from auditstack.cli import _register_bundled_stages
    _register_bundled_stages()

    # Replace content stage with V2 (chunk-level, deterministic + rubric)
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location(
        "content_stage_v2",
        "context/knowledge/visibility-framework/content_stage_v2.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["content_stage_v2"] = mod
    spec.loader.exec_module(mod)
    REGISTRY.unregister("content")
    REGISTRY.register(mod.ContentStageV2(max_pages=10))

    # Add Layer 3 External Presence stage
    spec3 = importlib.util.spec_from_file_location(
        "layer3_stage",
        "context/knowledge/visibility-framework/layer3_stage.py"
    )
    mod3 = importlib.util.module_from_spec(spec3)
    sys.modules["layer3_stage"] = mod3
    spec3.loader.exec_module(mod3)
    # Remove auditstack's entity stage (ours is more comprehensive)
    REGISTRY.unregister("entity")
    REGISTRY.register(mod3.ExternalPresenceStage())

    # Run pipeline
    print(f"\nRunning audit on {args.url}...\n")
    pipeline = Pipeline()


    result = pipeline.run(ctx)
    print(f"\nAudit complete!")
    print(f"Snapshot path: {result.path}")
    # Load the snapshot to show scores
    import json
    snap_file = result.path + "/snapshot.json"
    if os.path.exists(snap_file):
        with open(snap_file) as f:
            snap = json.load(f)
        print(f"Composite score: {snap.get('composite_score')}")
        print(f"Audit quality: {snap.get('audit_quality_score')}")
        print(f"Layer scores: {snap.get('layer_scores')}")


if __name__ == "__main__":
    main()
