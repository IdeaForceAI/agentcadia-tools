#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys
import urllib.parse
import urllib.request
import urllib.error


def http_json(url, method='GET', payload=None):
    headers = {}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        body = response.read().decode('utf-8')
        return json.loads(body)


def parse_args():
    parser = argparse.ArgumentParser(description='Run Agentcadia eval flows from CLI')
    subparsers = parser.add_subparsers(dest='action', required=True)

    start = subparsers.add_parser('start')
    start.add_argument('--origin', required=True)
    start.add_argument('--agent-name', default='')
    start.add_argument('--agent-id', default='')
    start.add_argument('--model', default='')
    start.add_argument('--language', choices=['zh', 'en'], default='en')

    status = subparsers.add_parser('status')
    status.add_argument('--origin', required=True)
    status.add_argument('--session-id', required=True)

    answer = subparsers.add_parser('answer')
    answer.add_argument('--origin', required=True)
    answer.add_argument('--session-id', required=True)
    answer.add_argument('--hash', required=True)
    answer_group = answer.add_mutually_exclusive_group(required=True)
    answer_group.add_argument('--answers-file', default='')
    answer_group.add_argument('--answers-json', default='')

    result = subparsers.add_parser('result')
    result.add_argument('--origin', required=True)
    result.add_argument('--session-id', required=True)

    return parser.parse_args()


def load_answers(args):
    if getattr(args, 'answers_file', ''):
        return json.loads(pathlib.Path(args.answers_file).read_text(encoding='utf-8'))
    return json.loads(args.answers_json)


def main():
    args = parse_args()
    origin = args.origin.rstrip('/')

    if args.action == 'start':
        payload = {
            'agentId': args.agent_id or None,
            'agentName': args.agent_name or None,
            'model': args.model or None,
            'language': args.language,
        }
        print(json.dumps(http_json(f'{origin}/api/eval/start', method='POST', payload=payload), ensure_ascii=False, indent=2))
        return

    if args.action == 'status':
        url = f"{origin}/api/eval/session?id={urllib.parse.quote(args.session_id)}"
        print(json.dumps(http_json(url), ensure_ascii=False, indent=2))
        return

    if args.action == 'answer':
        payload = {
            'sessionId': args.session_id,
            'hash': args.hash,
            'answers': load_answers(args),
        }
        print(json.dumps(http_json(f'{origin}/api/eval/answer', method='POST', payload=payload), ensure_ascii=False, indent=2))
        return

    if args.action == 'result':
        url = f"{origin}/api/eval/result?id={urllib.parse.quote(args.session_id)}"
        print(json.dumps(http_json(url), ensure_ascii=False, indent=2))
        return


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        print(json.dumps({'success': False, 'error': f'HTTP {exc.code}', 'body': body}, ensure_ascii=False, indent=2))
        sys.exit(1)
    except Exception as exc:
        print(json.dumps({'success': False, 'error': str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(1)
