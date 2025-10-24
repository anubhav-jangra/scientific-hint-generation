import time
import openai
import backoff
import asyncio
from typing import List, Dict

def backoff_handler(details):
    print(
        f"Try: {details['tries']}, waiting {float(details['wait']) + 30} because: {details['exception']}"
    )
    time.sleep(30)

@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=20,
    raise_on_giveup=False,
    on_backoff=backoff_handler,
)

async def async_call_gpt(
    queries: List[str],
    engine: str = "text-davinci-002",
) -> List[Dict]:
    if "gpt" in engine:
        print('Sample query:', queries[0])
        print('#num queries:', len(queries))
        async_responses = [
            openai.ChatCompletion.acreate(
                model=engine,
                messages=[{"role": "user", "content": query}],
            )
            for query in queries
        ]
    elif "text-davinci" in engine:
        async_responses = [
            openai.Completion.acreate(
                model=engine,
                prompt=query,
            )
            for query in queries
        ]
    else:
        raise ValueError(f"Unknown engine: {engine}")

    return await asyncio.gather(*async_responses)
