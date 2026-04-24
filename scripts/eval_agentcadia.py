#!/usr/bin/env python3
import argparse
import json
import pathlib
import shlex
import subprocess
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


def non_empty_or_none(value):
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def parse_args():
    parser = argparse.ArgumentParser(description='Run Agentcadia eval flows from CLI')
    subparsers = parser.add_subparsers(dest='action', required=True)

    start = subparsers.add_parser('start')
    start.add_argument('--origin', required=True)
    start.add_argument('--agent-name', default='')
    start.add_argument('--agent-id', default='')
    start.add_argument('--model', default='')
    start.add_argument('--language', choices=['zh', 'en'], default='en')
    start.add_argument('--question-set-slug', '--question_set_slug', dest='question_set_slug', default='')

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

    run = subparsers.add_parser('run', help='Run the full eval loop with an external answer command')
    run.add_argument('--origin', required=True)
    run.add_argument('--agent-name', default='')
    run.add_argument('--agent-id', default='')
    run.add_argument('--model', default='')
    run.add_argument('--language', choices=['zh', 'en'], default='en')
    run.add_argument('--question-set-slug', '--question_set_slug', dest='question_set_slug', default='')
    run.add_argument('--session-id', default='')
    run.add_argument('--answer-command', required=True, help='Shell command that reads current batch JSON from stdin and prints answers JSON to stdout')
    run.add_argument('--save-transcript', default='')
    run.add_argument('--quiet', action='store_true')

    return parser.parse_args()


def load_answers(args):
    if getattr(args, 'answers_file', ''):
        return json.loads(pathlib.Path(args.answers_file).read_text(encoding='utf-8'))
    return json.loads(args.answers_json)


def build_start_payload(args):
    payload = {
        'agentId': non_empty_or_none(getattr(args, 'agent_id', '')),
        'agentName': non_empty_or_none(getattr(args, 'agent_name', '')),
        'model': non_empty_or_none(getattr(args, 'model', '')),
        'language': args.language,
        'questionSetSlug': non_empty_or_none(getattr(args, 'question_set_slug', '')),
    }
    return {key: value for key, value in payload.items() if value is not None}


def print_log(enabled, message):
    if enabled:
        print(message, file=sys.stderr)


def run_answer_command(command, batch_payload):
    completed = subprocess.run(
        command,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        input=json.dumps(batch_payload, ensure_ascii=False),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f'answer command failed with exit code {completed.returncode}: {completed.stderr.strip() or completed.stdout.strip()}'
        )

    stdout = completed.stdout.strip()
    if not stdout:
        raise RuntimeError('answer command produced empty stdout')

    try:
        answers = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'answer command did not output valid JSON: {exc}') from exc

    if not isinstance(answers, list):
        raise RuntimeError('answer command must output a JSON array of answers')
    return answers


def save_transcript(path, transcript):
    if not path:
        return
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding='utf-8')


def run_eval_loop(args, origin):
    verbose = not args.quiet
    transcript = {
        'origin': origin,
        'questionSetSlug': non_empty_or_none(args.question_set_slug),
        'sessionId': non_empty_or_none(args.session_id),
        'steps': [],
    }

    if args.session_id:
        session_id = args.session_id
        print_log(verbose, f'[eval] resuming session {session_id}')
        current = http_json(f"{origin}/api/eval/session?id={urllib.parse.quote(session_id)}")
        transcript['steps'].append({'action': 'status', 'response': current})
    else:
        start_payload = build_start_payload(args)
        print_log(
            verbose,
            '[eval] starting session' + (
                f" (questionSetSlug={start_payload.get('questionSetSlug')})" if start_payload.get('questionSetSlug') else ''
            ),
        )
        current = http_json(f'{origin}/api/eval/start', method='POST', payload=start_payload)
        transcript['steps'].append({'action': 'start', 'payload': start_payload, 'response': current})
        session_id = current.get('sessionId') or current.get('session_id')

    if not session_id:
        raise RuntimeError('missing sessionId in eval response')

    transcript['sessionId'] = session_id

    while True:
        status = current.get('status')
        batch = current.get('batch')
        progress = current.get('progress') or {}

        if status == 'completed' and not batch:
            print_log(verbose, '[eval] session already completed, fetching result')
            result = http_json(f"{origin}/api/eval/result?id={urllib.parse.quote(session_id)}")
            transcript['steps'].append({'action': 'result', 'response': result})
            transcript['result'] = result
            save_transcript(args.save_transcript, transcript)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if not batch:
            print_log(verbose, '[eval] batch missing in current payload, fetching status')
            current = http_json(f"{origin}/api/eval/session?id={urllib.parse.quote(session_id)}")
            transcript['steps'].append({'action': 'status', 'response': current})
            batch = current.get('batch')
            if not batch and current.get('status') == 'completed':
                continue
            if not batch:
                raise RuntimeError('session is in progress but no batch payload was returned')

        batch_index = batch.get('index')
        batch_total = progress.get('batchTotal', '?')
        dimension = batch.get('dimension', 'unknown')
        print_log(verbose, f'[eval] answering batch {batch_index + 1 if isinstance(batch_index, int) else "?"}/{batch_total} dimension={dimension}')

        answer_request_payload = {
            'sessionId': session_id,
            'status': status,
            'progress': progress,
            'batch': batch,
        }
        answers = run_answer_command(args.answer_command, answer_request_payload)
        submit_payload = {
            'sessionId': session_id,
            'hash': batch['hash'],
            'answers': answers,
        }
        current = http_json(f'{origin}/api/eval/answer', method='POST', payload=submit_payload)
        transcript['steps'].append({
            'action': 'answer',
            'batchIndex': batch_index,
            'dimension': dimension,
            'request': submit_payload,
            'response': current,
        })

        if current.get('done'):
            print_log(verbose, '[eval] all batches answered, fetching result')
            result = http_json(f"{origin}/api/eval/result?id={urllib.parse.quote(session_id)}")
            transcript['steps'].append({'action': 'result', 'response': result})
            transcript['result'] = result
            save_transcript(args.save_transcript, transcript)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return


def main():
    args = parse_args()
    origin = args.origin.rstrip('/')

    if args.action == 'start':
        payload = build_start_payload(args)
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

    if args.action == 'run':
        run_eval_loop(args, origin)
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
