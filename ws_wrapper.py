import asyncio
import aiohttp
import sys
import subprocess
import argparse
import json
import os

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="WebSocket URL")
    parser.add_argument("--trace-id", required=True, help="Trace ID for the job")
    parser.add_argument("--command", nargs=argparse.REMAINDER, help="Command to run")
    args = parser.parse_args()

    command = args.command
    if not command:
        print("No command specified")
        sys.exit(1)

    
    print(f"Connecting to {args.url} for trace {args.trace_id}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(args.url) as ws:
                await ws.send_json({
                    "type": "auth",
                    "trace_id": args.trace_id
                })
                
                print(f"Running command: {' '.join(command)}")
                
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    decoded_line = line.decode('utf-8', errors='replace').strip()
                    if decoded_line:
                        print(decoded_line)
                        await ws.send_json({
                            "type": "log",
                            "content": decoded_line
                        })
                
                return_code = await process.wait()
                
                await ws.send_json({
                    "type": "complete",
                    "exit_code": return_code
                })
                
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"WebSocket/Execution Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
