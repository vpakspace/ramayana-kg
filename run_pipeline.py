#!/usr/bin/env python3
"""CLI for Ramayana Knowledge Graph pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from ramayana_kg.config import settings


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_all(args):
    from ramayana_kg.pipeline import run_full_pipeline
    result = run_full_pipeline()
    print(json.dumps(result, indent=2, default=str))


def cmd_download(args):
    from ramayana_kg.pipeline import step_download
    path = step_download()
    print(f"Downloaded: {path}")


def cmd_parse(args):
    from ramayana_kg.pipeline import step_parse
    verses = step_parse()
    print(f"Parsed {len(verses)} verses")
    # Show summary by kanda
    kanda_counts: dict[str, int] = {}
    for v in verses:
        kanda_counts[v.kanda] = kanda_counts.get(v.kanda, 0) + 1
    for kanda, count in sorted(kanda_counts.items()):
        print(f"  {kanda}: {count} verses")


def cmd_extract(args):
    from ramayana_kg.pipeline import step_extract, step_parse
    verses = step_parse()
    result = step_extract(verses)
    print(f"Entities: {len(result['entities'])}")
    print(f"Relationships: {len(result['relationships'])}")


def cmd_build(args):
    from ramayana_kg.pipeline import get_driver, step_build, step_extract, step_parse
    verses = step_parse()
    extraction = step_extract(verses)
    driver = get_driver()
    try:
        result = step_build(driver, verses, extraction)
        print(json.dumps(result, indent=2))
    finally:
        driver.close()


def cmd_embed(args):
    from ramayana_kg.pipeline import get_driver, step_embed, step_parse
    verses = step_parse()
    driver = get_driver()
    try:
        result = step_embed(driver, verses)
        print(json.dumps(result, indent=2))
    finally:
        driver.close()


def cmd_query(args):
    from ramayana_kg.pipeline import get_driver
    from ramayana_kg.rag.generator import generate_answer
    driver = get_driver()
    try:
        result = generate_answer(args.question, driver, mode=args.mode)
        print(f"\n{'='*60}")
        print(f"Question: {args.question}")
        print(f"Mode: {result.mode}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"{'='*60}")
        print(f"\n{result.answer}\n")
        if result.sources:
            print(f"--- Sources ({len(result.sources)}) ---")
            for src in result.sources:
                print(f"  [{src.verse_id}] score={src.score:.3f}")
    finally:
        driver.close()


def cmd_stats(args):
    from ramayana_kg.graph.schema import get_stats
    from ramayana_kg.pipeline import get_driver
    driver = get_driver()
    try:
        stats = get_stats(driver, database=settings.neo4j_database)
        print(json.dumps(stats, indent=2))
    finally:
        driver.close()


def cmd_clear(args):
    from ramayana_kg.graph.schema import clear_database
    from ramayana_kg.pipeline import get_driver
    if not args.yes:
        confirm = input("Are you sure you want to clear the database? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted.")
            return
    driver = get_driver()
    try:
        count = clear_database(driver, database=settings.neo4j_database)
        print(f"Deleted {count} nodes")
    finally:
        driver.close()


def main():
    parser = argparse.ArgumentParser(description="Ramayana Knowledge Graph CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("all", help="Run full pipeline")
    subparsers.add_parser("download", help="Download Ramayana text")
    subparsers.add_parser("parse", help="Parse text into verses")
    subparsers.add_parser("extract", help="Extract entities and relationships")
    subparsers.add_parser("build", help="Build knowledge graph")
    subparsers.add_parser("embed", help="Embed verses and entities")

    query_parser = subparsers.add_parser("query", help="Query the knowledge graph")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument("--mode", choices=["hybrid", "vector", "graph"], default="hybrid")

    subparsers.add_parser("stats", help="Show graph statistics")

    clear_parser = subparsers.add_parser("clear", help="Clear the database")
    clear_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "all": cmd_all,
        "download": cmd_download,
        "parse": cmd_parse,
        "extract": cmd_extract,
        "build": cmd_build,
        "embed": cmd_embed,
        "query": cmd_query,
        "stats": cmd_stats,
        "clear": cmd_clear,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
