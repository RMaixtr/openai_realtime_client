import asyncio
import os
from prompts import prompts
from openai_realtime_client import RealtimeClient, WmixHandler, TurnDetectionMode
from llama_index.core.tools import FunctionTool

# Add your own tools here!
# NOTE: FunctionTool parses the docstring to get description, the tool name is the function name
def motion(name: str) -> str:
    """
    当你需要动时调用这个函数，只能传入跳舞，坐下或者疑惑，当不是跳舞或者坐下时传入疑惑
    When you call this function when you need to move, you can only pass 跳舞, 坐下, or 疑惑, and when you are not dancing or sitting, you can pass 疑惑
    """
    print(name)
    if name == "跳舞":
        return "正在跳舞"
    elif name == "坐下":
        return "正在坐下"
    else:
        return "疑惑"

tools = [FunctionTool.from_defaults(fn=motion)]

async def main():
    audio_handler = WmixHandler()
    # input_handler = InputHandler()
    # input_handler.loop = asyncio.get_running_loop()
    
    client = RealtimeClient(
        api_key=os.environ.get("OPENAI_API_KEY"),
        # instructions=prompts,
        on_text_delta=lambda text: print(f"\nAssistant: {text}", end="", flush=True),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        on_interrupt=lambda: audio_handler.stop_playback_immediately(),
        turn_detection_mode=TurnDetectionMode.SERVER_VAD,
        tools=tools,
    )

    # Start keyboard listener in a separate thread
    # listener = keyboard.Listener(on_press=input_handler.on_press)
    # listener.start()
    
    try:
        await client.connect()
        message_handler = asyncio.create_task(client.handle_messages())
        
        print("Connected to OpenAI Realtime API!")
        
        # Start continuous audio streaming
        streaming_task = asyncio.create_task(audio_handler.start_streaming(client))
        
        # Simple input loop for quit command
        while True:
            await asyncio.sleep(1)
            # command, _ = await input_handler.command_queue.get()
            
            # if command == 'q':
            #     break
            
    # except Exception as e:
    #     print(f"Error: {e}")
    finally:
        audio_handler.cleanup()
        await client.close()

if __name__ == "__main__":
    print("Starting Realtime API CLI with Server VAD...")
    asyncio.run(main())
