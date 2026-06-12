import json, os, re
from openai import OpenAI
from tools import create_Code_File, execute_Code, generate_Manim_Code, tools
import uuid
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

SYSTEM_PROMPT = """
You are an animation planning expert for Manim videos.

When a user requests a video you MUST follow 
these steps IN ORDER without stopping:

STEP 1: Call generate_Manim_Code with a detailed plan
STEP 2: Call create_Code_File to save the code to disk
STEP 3: Call execute_Code to render the video

CRITICAL RULES:
- You MUST call ALL THREE tools every single time
- Do NOT stop after generate_Manim_Code
- Do NOT respond to the user until execute_Code is called
- Do NOT say the code is ready until the video is rendered
- The workflow is only complete after execute_Code finishes

You are NOT done until execute_Code has been called.

Your plan argument MUST include:
- Topic name
- Total number of scenes
- For each scene:
  * Scene title
  * Objects to create (shapes, colors, sizes)
  * Animations to use (FadeIn, GrowFromCenter, etc.)
  * Text and labels needed
  * Cleanup instructions

Example of a good plan argument:
Topic: Photosynthesis
Total Scenes: 3

Scene 1 - Sunlight:
- Objects: Yellow circle (sun), Green rectangle (leaf)
- Animations: GrowFromCenter sun, Create arrow to leaf
- Text: 'Sunlight' label below sun
- Cleanup: FadeOut scene1_group

Scene 2 - Inputs:
...
"""

sessions = {}  # Global store

def extract_scene_class(code: str) -> str:
    match = re.search(r'class\s+(\w+)\s*\(\s*Scene\s*\)', code)
    if match:
        return match.group(1)
    return "GeneratedScene"

def run_agent_loop(message_history, session_id, tools):
    tools_called = []

    while True:
        response = client.chat.completions.create(
            model="gpt-oss-120b",
            messages=message_history,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        message_history.append(message)

        if not message.tool_calls:
            print("🤖", message.content)
            break

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            if tool_name in tools_called:
                continue

            tools_called.append(tool_name)
            print(f"🛠️ Calling: {tool_name}")

            if tool_name == "generate_Manim_Code":
                sessions[session_id]["plan"] = tool_args.get("plan", "")
                result = generate_Manim_Code(tool_args["plan"])
                sessions[session_id]["generated_code"] = result
                result = "Code generated successfully"

            elif tool_name == "create_Code_File":
                code = sessions[session_id]["generated_code"]
                result = create_Code_File(code, session_id)

            elif tool_name == "execute_Code":
                max_retries = 3
                attempt = 0
                result = None

                while attempt < max_retries:
                    attempt += 1
                    print(f"🔄 Attempt {attempt}/{max_retries}")
                    scene_class = extract_scene_class(
                        sessions[session_id]["generated_code"]
                    )
                    result = execute_Code(session_id, scene_class)

                    if not result.startswith("Error:"):
                        print(f"✅ Success on attempt {attempt}")
                        break

                    if attempt == max_retries:
                        print("❌ All 3 attempts failed")
                        break

                    fixed_code = generate_Manim_Code(
                        f"""
                            Error: {result}
                            Plan: {sessions[session_id].get('plan', '')}
                            Broken code: {sessions[session_id]['generated_code']}
                            Fix ONLY the error. Return complete corrected code.
                        """
                    )
                    sessions[session_id]["generated_code"] = fixed_code
                    create_Code_File(fixed_code, session_id)

                sessions[session_id]["video_path"] = result

            else:
                result = f"Unknown tool: {tool_name}"

            message_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

            if tool_name == "execute_Code":
                print(f"🎬 Video: {sessions[session_id]['video_path']}")
                break

        if "execute_Code" in tools_called:
            break


def run_feedback_round(session_id, feedback):
    print("🔄 Applying feedback...")

    # Step 1 — Directly generate refined code
    # No tool calling needed here — just call function directly
    refined_code = generate_Manim_Code(
        f"""
Previous working code:
{sessions[session_id]['generated_code']}

User feedback:
{feedback}

Instructions:
- Keep everything the user did NOT mention
- Only change what user specifically asked for
- Return the COMPLETE modified code
- Use the SAME class name as before
"""
    )

    # Step 2 — Update session with new code
    sessions[session_id]["generated_code"] = refined_code

    # Step 3 — Overwrite SAME file with same session_id
    create_Code_File(refined_code, session_id)
    print(f"✅ File updated for session {session_id}")

    # Step 4 — Execute same file with retry loop
    max_retries = 3
    attempt = 0
    result = None

    while attempt < max_retries:
        attempt += 1
        print(f"🔄 Attempt {attempt}/{max_retries}")

        scene_class = extract_scene_class(
            sessions[session_id]["generated_code"]
        )
        result = execute_Code(session_id, scene_class)

        if not result.startswith("Error:"):
            print(f"✅ Success on attempt {attempt}")
            break

        print(f"❌ Attempt {attempt} failed")

        if attempt == max_retries:
            print("❌ All 3 attempts failed")
            break

        # Fix error
        fixed_code = generate_Manim_Code(
            f"""
Error: {result}
Previous code: {sessions[session_id]['generated_code']}
Fix ONLY the error. Return complete corrected code.
"""
        )
        sessions[session_id]["generated_code"] = fixed_code
        create_Code_File(fixed_code, session_id)

    sessions[session_id]["video_path"] = result
    return result


def run_agent():
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {
        "generated_code": None,
        "messages": [],
        "video_path": None,
        "plan": None,
        "version": 0
    }

    message_history = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    user_query = input("Generate a video: ")
    message_history.append({"role": "user", "content": user_query})

    # First generation — full agent loop
    run_agent_loop(message_history, session_id, tools)

    # Feedback loop
    while True:
        print(f"\n📽️  Video: {sessions[session_id]['video_path']}")
        feedback = input(
            "\nSatisfied? (yes to exit / type feedback): "
        ).strip()

        if feedback.lower() in ["yes", "y", ""]:
            print("🎉 Enjoy your video!")
            break

        # Feedback round — bypass agent loop entirely
        # Directly refine and re-execute same file
        run_feedback_round(session_id, feedback)

run_agent()