#!/usr/bin/env python3
"""
DefHack CLI - Easy command-line interface for data input
Usage:
  python defhack_cli.py obs --what "T-72 Tank" --amount 2 --mgrs "35VLG8472571866" --observer "Alpha6"
  python defhack_cli.py doc --file "report.pdf" --title "Tactical Analysis" --type "doctrinal"
  python defhack_cli.py search --query "BTG tactics"
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from defhack_unified_input import DefHackClient

def add_observation_cli(args):
    """Add sensor observation via CLI"""
    client = DefHackClient()
    
    # Build observation from CLI args
    observation = {
        "time": args.time or datetime.now(timezone.utc).isoformat(),
        "mgrs": args.mgrs,
        "what": args.what,
        "amount": args.amount,
        "confidence": args.confidence,
        "sensor_id": args.sensor_id or "CLI_INPUT",
        "unit": args.unit,
        "observer_signature": args.observer
    }
    
    # Remove None values
    observation = {k: v for k, v in observation.items() if v is not None}
    
    result = client.add_sensor_observation(observation)
    
    if 'report_id' in result:
        print(f"\n✅ Observation added successfully!")
        print(f"Report ID: {result['report_id']}")
    else:
        print(f"\n❌ Failed to add observation")
        sys.exit(1)

def upload_document_cli(args):
    """Upload intelligence document via CLI"""
    client = DefHackClient()
    
    metadata = {
        "title": args.title,
        "version": args.version,
        "lang": args.lang,
        "origin": args.origin,
        "adversary": args.adversary,
        "published_at": args.published_at,
        "classification": args.classification,
        "document_type": args.type
    }
    
    # Remove None values
    metadata = {k: v for k, v in metadata.items() if v is not None}
    
    result = client.upload_intelligence_document(args.file, **metadata)
    
    if 'doc_id' in result:
        print(f"\n✅ Document uploaded successfully!")
        print(f"Document ID: {result['doc_id']}")
        print(f"Chunks created: {result['chunks']}")
    else:
        print(f"\n❌ Failed to upload document")
        sys.exit(1)

def search_cli(args):
    """Search intelligence database via CLI"""
    client = DefHackClient()
    
    results = client.search(args.query, args.limit)
    
    if results:
        print(f"\n🔍 Search Results ({len(results)} found):")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            doc_id = result.get('doc_id', 'N/A')
            page = result.get('page', 'N/A')
            text = result.get('text', '')
            
            print(f"\n[{i}] Document ID: {doc_id}, Page: {page}")
            
            # Show first 200 characters
            if len(text) > 200:
                text = text[:200] + "..."
            print(f"Text: {text}")
            
    else:
        print(f"\n⚠️  No results found for: '{args.query}'")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="DefHack CLI - Easy interface for intelligence data input",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add tactical observation
  python defhack_cli.py obs --what "Infantry Squad" --amount 8 --mgrs "35VLG8472571866" --observer "Alpha6" --confidence 90
  
  # Upload intelligence document  
  python defhack_cli.py doc --file "report.pdf" --title "Tactical Analysis Report" --type "doctrinal"
  
  # Search database
  python defhack_cli.py search --query "BTG tactics" --limit 5
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Observation subcommand
    obs_parser = subparsers.add_parser('obs', help='Add tactical sensor observation')
    obs_parser.add_argument('--what', required=True, help='What was observed (e.g., "T-72 Tank")')
    obs_parser.add_argument('--mgrs', required=True, help='MGRS location (e.g., "35VLG8472571866")')
    obs_parser.add_argument('--observer', required=True, help='Observer signature/callsign')
    obs_parser.add_argument('--amount', type=float, help='Quantity observed')
    obs_parser.add_argument('--confidence', type=int, default=85, help='Confidence level (0-100)')
    obs_parser.add_argument('--sensor-id', help='Sensor/equipment ID')
    obs_parser.add_argument('--unit', help='Observing unit')
    obs_parser.add_argument('--time', help='Observation time (ISO 8601)')
    
    # Document subcommand
    doc_parser = subparsers.add_parser('doc', help='Upload intelligence document')
    doc_parser.add_argument('--file', required=True, help='Path to document file')
    doc_parser.add_argument('--title', required=True, help='Document title')
    doc_parser.add_argument('--version', help='Document version')
    doc_parser.add_argument('--lang', default='en', help='Language (ISO 639-1)')
    doc_parser.add_argument('--origin', help='Source organization')
    doc_parser.add_argument('--adversary', help='Adversary/subject focus')
    doc_parser.add_argument('--published-at', help='Publication date (YYYY-MM-DD)')
    doc_parser.add_argument('--classification', default='UNCLASSIFIED', help='Security classification')
    doc_parser.add_argument('--type', choices=['doctrinal', 'tactical', 'strategic', 'technical'], help='Document type')
    
    # Search subcommand  
    search_parser = subparsers.add_parser('search', help='Search intelligence database')
    search_parser.add_argument('--query', required=True, help='Search query')
    search_parser.add_argument('--limit', type=int, default=5, help='Maximum results to return')
    
    args = parser.parse_args()
    
    if args.command == 'obs':
        add_observation_cli(args)
    elif args.command == 'doc':
        upload_document_cli(args)
    elif args.command == 'search':
        search_cli(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()