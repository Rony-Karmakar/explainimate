import json
from openai import OpenAI
from tools import get_available_tools
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

all_tools = get_available_tools()

SYSTEM_PROMPT="""
You are an animation planning expert. 
When given a topic, think step by step and create 
a detailed plan for a Manim animation.

Your plan must include:
- How many scenes are needed
- What objects appear in each scene
- What animations happen (FadeIn, Transform, etc.)
- The logical sequence of the explanation
- What text/labels are needed

* Output JSON Format:
    { "step": "START" | "PLAN" | "OBSERVE" | "FINAL_OUTPUT" | "TOOLS", "content": "string", "tool": "string", "input": "string" }

CRITICAL RULE:
Output ONLY ONE JSON object per response.
Stop after each JSON and wait for the next instruction.
Do NOT output multiple steps in one response.

!!! You have 4 steps: START | PLAN | TOOLS | OBSERVE | FINAL_OUTPUT !!!

START: Here, START means that, the user gives the input to generate a video

PLAN: It means after getting the input you have to think about the problem and make plan for the next step, how should you approach that problem 

### There are tools available for you
TOOLS:
- generate_Manim_Code(cot_prompt: str): Takes cot_prompt (generate message_history including all steps) as an input string and return the manim code according to the user query
- create_Code_File(code: str, session_id): takes generated main code as input and create file and write the code in the created file
- execute_Code(session_id): It takes session_id and run a docker command to execute the code and it creates a folder called output to store the result(videos)

Example 1:
User: Generate a video of the photosynthesis process!
START: { "step": "START", "content": "Generate a video of the photosynthesis process" }
PLAN: { "step": "PLAN", "content": "Seems like user is interested to generate the photosynthesis process" }
PLAN: { "step": "PLAN": "content": "Lets see if we have any available tool from the list of available tools" }
PLAN: { "step": "PLAN": "content": "Great, we have generate_Manim_Code tool available for this query." }
PLAN: { "step": "PLAN": "content": "I need to call generate_Manim_Code tool " }

TOOLS: { 
  "step": "TOOLS", 
  "tool": "generate_Manim_Code", 
  "input": "
    Topic: Photosynthesis Process
    Total Scenes: 3 or more (it is not specific number)

    Scene 1 - Light Energy:
    - Objects: Sun circle (YELLOW), Leaf shape (GREEN), Arrow
    - Animations: GrowFromCenter sun, Create arrow pointing to leaf
    - Text: 'Sunlight' label below sun
    - Cleanup: FadeOut scene1_group

    Scene 2 - Inputs:
    - Objects: CO2 text, Water molecule, Arrows pointing into leaf
    - Animations: FadeIn CO2, FadeIn H2O, Create arrows
    - Text: Labels for CO2 and H2O
    - Cleanup: FadeOut scene2_group

    Scene 3 - Output:
    - Objects: Glucose molecule (ORANGE), O2 text (BLUE)
    - Animations: GrowFromCenter glucose, FadeIn oxygen
    - Text: 'Glucose' and 'Oxygen' labels
    - Cleanup: FadeOut scene3_group

    Scene 4 - ... continue till Total Scenes
  "
}

OBSERVE: { "step": "OBSERVE", "tool": "generate_Manim_Code", "output: "Oh, I generate the code" }

FINAL_OUTPUT: {"step": "OUTPUT", 
    "content": "
        class GeneratedScene(Scene):
            def construct(self):

                # --- Scene 1 ---
                title = Text("Photosynthesis", font_size=48)
                title.to_edge(UP)
                self.play(FadeIn(title))

                scene1_group = VGroup()
                
                sun = Circle(radius=0.8, color=YELLOW, 
                            fill_opacity=0.8)
                sun_label = Text("Sunlight", 
                                font_size=24).next_to(sun, DOWN)
                scene1_group.add(sun, sun_label)
                
                self.play(GrowFromCenter(sun))
                self.play(FadeIn(sun_label))
                self.wait(1.5)
                
                # Always clean up before next scene
                self.play(FadeOut(scene1_group))

                # --- Scene 2 ---
                scene2_group = VGroup()
                # next scene content here...
                self.play(FadeOut(scene2_group))
" }

TOOLS: { 
  "step": "TOOLS", 
  "tool": "create_Code_File", 
  "input": "code, session_id"
}

OBSERVE: { "step": "OBSERVE", "tool": "create_Code_File", "output: "Great, I just create the file and add the code in the file" }

TOOLS: { 
  "step": "TOOLS", 
  "tool": "execute_Code", 
  "input": "session_id"
}

OBSERVE: { "step": "OBSERVE", "tool": "execute_Code", "output: "Great, code execution is completed" }

FINAL_OUTPUT: { "step": "FINAL_OUTPUT", content: "Now enjoy your video bro😎"}
"""
#OBSERVE | ERROR |

class MyOutputFormat(BaseModel):
    step: str = Field(..., description="The ID of the step. Example: PLAN, OUTPUT, TOOL, etc")
    content: Optional[str] = Field(None, description="The optional string content for the step")
    tool: Optional[str] = Field(None, description="The ID of the tool to call.")
    input: Optional[str] = Field(None, description="The input params for the tool")

sessions = {}  # Global store

def run_agent():
    # Session created fresh for every call
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {
        "generated_code": None,
        "messages": [],
        "video_path": None
    }

    message_history = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    sessions[session_id]["messages"] = message_history

    user_query = input("Generate a video: ")
    message_history.append({"role": "user", "content": user_query})

    while True:
        response = client.chat.completions.parse(
            model="gpt-oss-120b",
            response_format=MyOutputFormat,
            messages=message_history
        )

        raw_result = response.choices[0].message.content
        message_history.append({"role": "assistant", "content": raw_result})
        parsed_result = response.choices[0].message.parsed

        if parsed_result and parsed_result.step == 'START':
            print("🔥", parsed_result.content)
            continue

        if parsed_result and parsed_result.step == 'PLAN':
            print("🧠", parsed_result.content)
            continue

        if parsed_result and parsed_result.step == 'OBSERVE':
            print("👁️", parsed_result.content)
            continue

        if parsed_result and parsed_result.step == 'TOOLS':
            tool_to_call = parsed_result.tool
            tool_input = parsed_result.input
            print(f"🛠️: {tool_to_call} ({tool_input})")

            if tool_to_call == "generate_Manim_Code":
                tool_response = all_tools[tool_to_call](tool_input)
                sessions[session_id]["generated_code"] = tool_response
                tool_response = "Code generated successfully"

            elif tool_to_call == "create_Code_File":
                code = sessions[session_id]["generated_code"]
                tool_response = all_tools[tool_to_call](code, session_id)

            elif tool_to_call == "execute_Code":
                tool_response = all_tools[tool_to_call](session_id)
                sessions[session_id]["video_path"] = tool_response

            print(f"✅: {tool_to_call} = {tool_response}")
            message_history.append({
                "role": "user",
                "content": json.dumps({
                    "step": "OBSERVE",
                    "tool": tool_to_call,
                    "input": tool_input,
                    "output": tool_response
                })
            })
            continue

        if parsed_result and parsed_result.step == "FINAL_OUTPUT":
            print("🤖", parsed_result.content)
            print(f"🎬 Video: {sessions[session_id]['video_path']}")
            break

# Call it
run_agent()