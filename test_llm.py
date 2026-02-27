import asyncio
import sys
import traceback
sys.path.append('.')
from app.core.llm import get_llm
async def test_llm():
    print('Testing LLM connection to OpenRouter...')
    try:
        llm = get_llm()
        response = llm.invoke('Hi! Are you ready to assist as a government agent? Keep your answer to one polite sentence.')
        print('\n--- LLM Response ---')
        print(response.content)
        print('--------------------\n')
        print('SUCCESS: LLM connection established.')
    except Exception as e:
        print(f'ERROR: LLM connection failed: {e}')
        traceback.print_exc()
        sys.exit(1)
if __name__ == '__main__':
    asyncio.run(test_llm())
