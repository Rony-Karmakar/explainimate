from openai import OpenAI
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

def generate_Manim_Code(plan: str):
    CODE_SYSTEM_PROMPT = """
        You are an expert Manim v0.18 Python code writer.
        You will receive a detailed animation plan from a 
        planning agent. Your ONLY job is to convert that 
        plan into perfect executable Manim Python code.

        ## YOUR ROLE
        - You do NOT think or plan
        - You do NOT ask questions
        - You ONLY write clean Manim Python code
        - You write exactly what the plan tells you to animate

        ## OUTPUT FORMAT
        - Output raw Python code ONLY
        - No markdown code blocks
        - No explanations before or after
        - No comments unless they are inside the code

        ## MANDATORY CODE STRUCTURE
        from manim import *

        class GeneratedScene(Scene):
            def construct(self):
                # your code here

        ## CORRECT MANIM APIs (FOLLOW STRICTLY)
        Text()          not TextMobject()
        MathTex()       not TexMobject()
        Create()        not ShowCreation()
        FadeIn()        not FadeInFrom()
        VGroup()        not Group() for mobjects
        .arrange()      not .to_center()
        code.code[]     not code.get_code_mobject()

        ## SCENE HYGIENE RULES
        - Group every scene elements into one VGroup
        - Always FadeOut the VGroup before next scene
        - Never hardcode same coordinates in back to back scenes
        - Always use .next_to() for labels not hardcoded positions

        ## ANIMATION QUALITY RULES
        - Never draw a plain shape and just label it
        - Use GrowFromCenter() Create() Indicate() Transform()
        - Use ReplacementTransform() to evolve shapes smoothly
        - Add self.wait(1.5) after every key concept
        - Keep main title persistent at top using .to_edge(UP)

        ## ARRAY AND SORTING ALGORITHM RULES (CRITICAL)
        - Create ALL boxes and numbers ONCE at the start
        - Store EVERY number in a tracked variable, never lose reference
        - NEVER create new Text() inside a loop without storing reference
        - NEVER instantiate a new Text() on top of an existing one
        - Use ReplacementTransform() for ALL element movements
        - Track sorted and unsorted partitions in separate VGroups
        - Sorted partition and unsorted partition must NEVER 
          share same screen coordinates
        - When highlighting current key element use 
          Indicate() or SurroundingRectangle() not a new object
        - Always remove SurroundingRectangle before next step
          using FadeOut()
        - For swapping two elements ALWAYS do:
            self.play(
                elem1.animate.move_to(elem2.get_center()),
                elem2.animate.move_to(elem1.get_center())
            )
          NEVER create new Text objects for swapped positions

        ## CORRECT INSERTION SORT PATTERN
        from manim import *

        class GeneratedScene(Scene):
            def construct(self):
                # Create array ONCE
                values = [4, 6, 1, 3]
                boxes = VGroup(*[Square(side_length=1) 
                                for _ in values])
                numbers = VGroup(*[Text(str(v), font_size=36) 
                                  for v in values])
                
                # Position everything ONCE
                boxes.arrange(RIGHT, buff=0.2).move_to(ORIGIN)
                for i, num in enumerate(numbers):
                    num.move_to(boxes[i].get_center())
                
                self.play(Create(boxes), FadeIn(numbers))
                self.wait(1)
                
                # Highlight key element with SurroundingRectangle
                key_rect = SurroundingRectangle(
                    boxes[1], color=ORANGE, buff=0
                )
                self.play(Create(key_rect))
                self.wait(1)
                
                # Move elements using animate, NOT new Text()
                self.play(
                    numbers[0].animate.move_to(boxes[1].get_center()),
                    numbers[1].animate.move_to(boxes[0].get_center())
                )
                self.wait(1)
                
                # Remove highlight before next step
                self.play(FadeOut(key_rect))

        ## EXAMPLE OF GOOD CODE STRUCTURE
        from manim import *

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
    """

    response = client.chat.completions.create(
        model="zai-glm-4.7",
        messages=[
            {
                "role": "system", "content": CODE_SYSTEM_PROMPT
            },
            {
                "role": "user", "content": plan
            }
        ],

    )

    return response.choices[0].message.content

def create_Code_File(code, session_id):
    # Keep this exactly as you wrote it. It writes locally to your host's scenes folder.
    os.makedirs("scenes", exist_ok=True)
    filename = f"scenes/scene_{session_id}.py"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(code)

    return filename

import subprocess
import os

def execute_Code(session_id, scene_class="GeneratedScene"):
    # Ensure we are mapping inside the backend folder context
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs("output", exist_ok=True)
    result = subprocess.run([
        "docker", "compose", "exec", "-T", "manim",
        "manim", "-qm",
        f"/manim/scene_{session_id}.py",
        scene_class,
        "--media_dir", "/output"  # <--- FIX: Corrected back to standard Manim flag
    ],
    capture_output=True,
    text=True,
    cwd=backend_dir,
    encoding="utf-8"
    )
    
    if result.returncode == 0:
        # Manim paths nested with standard --media_dir logic:
        # output/videos/scene_{session_id}/720p30/{scene_class}.mp4
        video_path = os.path.join(
            backend_dir, "output", "videos", f"scene_{session_id}", "720p30", f"{scene_class}.mp4"
        )
        
        if os.path.exists(video_path):
            return video_path
        else:
            return f"Error: Render succeeded but file missing at expected path: {video_path}"
    else:
        return f"Error: {result.stderr}"

def get_available_tools():
    
    return {
        'generate_Manim_Code': generate_Manim_Code,
        'create_Code_File': create_Code_File,
        'execute_Code': execute_Code
    }