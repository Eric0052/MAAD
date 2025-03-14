from metagpt.actions import Action
from pathlib import Path
from metagpt.roles import Role
import asyncio
from metagpt.logs import logger
from metagpt.schema import Message
import json
import os

class Modeling(Action):
    #architectural documentation
    PROMPT_TEMPLATE1: str = """"
    Here are: \n
    (1) architecturally significant requirements: {ASR}\n
    (2) functional requirements: {FR}\n
    (3) non-functional requirements: {NFR}\n
    (4) design constraints: {DC}\n

    Based on the provided details, please generate the architectural documentation that documentation should serve as high-level guidance and background information for the entire system, includeing:
    1.Overall Architecture Design Ideas: Provide an overview of the architectural approach and strategy.
    2.Goals: Define the primary objectives that the architecture aims to achieve.
    3.Design Principles: Describe the guiding principles that influence design decisions.
    4.Key Technologies: Identify the critical technologies and tools to be used in the system.
    5.Constraints: Summarize any design constraints and potential risks that need to be addressed.
    """

    #architectural views and decisions
    PROMPT_TEMPLATE2: str = """
    Here are: \n
    (1) architecturally significant requirements: {ASR}\n
    (2) functional requirements: {FR}\n
    (3) non-functional requirements: {NFR}\n
    (4) design constraints: {DC}\n
    Based on the provided requirements, please generate the requisite architectural views using PlantUML syntax. Ensure that your PlantUML syntax is correct and that the diagrams are clear and informative. Meanwhile, record the architectural decisions (List and explain the key architectural decisions made during the design process) to explain the design choices made in response to the provided requirements and constraints. 
    1. Logic View: illustrate the primary functional modules of the system and show how they interact or depend on one another.
    2. Process View: deal with the dynamic aspects of the system, explains the system processes and how they communicate, and focuses on the run time behavior of the system. The process view addresses concurrency, distribution, integrator, performance, and scalability, etc.
    3. Development View: aka implementation views, illustrates a system from a programmer's perspective and is concerned with software management.
    4. Physical Views: depicts the system from a system engineer's point of view. It is concerned with the topology of software components on the physical layer as well as the physical connections between these components.
    5. Scenario View: depict an architecture is illustrated using a small set of use cases, or scenarios. The scenarios describe sequences of interactions between objects and between processes. They are used to identify architectural elements and to illustrate and validate the architecture design. They also serve as a starting point for tests of an architecture prototype.
    6. Architectural Decisions: Record key architectural decisions, selected alternatives and their trade-offs, helping the team understand the reasons behind the decisions and providing reference for possible subsequent adjustments.

    Structure your outputs as follows:
    1. [logic view]\n
    @startuml
    xxxx
    @enduml
    2. [process view]\n
    @startuml
    xxxx
    @enduml
    ……
    6. [Architectural decisions]\n
    [Decision 1]: Provide a brief explanation of the decision and its rationale.
    [Decision 2]: Provide a brief explanation of the decision and its rationale.
    ......
    """

    PROMPT_TEMPLATE3: str = """
    Here are: \n
    (1) architecturally significant requirements: {ASR}\n
    (2) functional requirements: {FR}\n
    (3) non-functional requirements: {NFR}\n
    (4) design constraints: {DC}\n
    Based on the requirements, is it necessary to generate other architectural views besides Logic View, Process View, Development View, Physical View, and Scenario View? 
    If so, explain the necessity and generate the additional architectural views using PlantUML syntax. \n
    """
    name: str = "Modeling"

    output_root : Path = Path("output//Modeler")

    #根据json文件中的配置信息，生成对应的文件名
    @classmethod
    def set_output_root(cls, output_root: Path):
        cls.output_root = output_root

    async def run(self, ASR: str, FR: str, NFR: str, DC: str):
        prompt1 = self.PROMPT_TEMPLATE1.format(ASR = ASR, FR = FR, NFR = NFR, DC = DC)  
        rsp = await self._aask(prompt1)
        file_path = self.file_name("AD")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
        prompt2 = self.PROMPT_TEMPLATE2.format(ASR = ASR, FR = FR, NFR = NFR, DC = DC) 
        rsp = await self._aask(prompt2)
        file_path = self.file_name("AV")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
        prompt3 = self.PROMPT_TEMPLATE3.format(ASR = ASR, FR = FR, NFR = NFR, DC = DC) 
        rsp = await self._aask(prompt3)
        file_path = self.file_name("AD_AV")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
    
    @classmethod
    def file_name(cls, name : str) -> str:
        output_dir = cls.output_root
        output_dir.mkdir(parents=True, exist_ok=True)
        # 查找现有文件并生成新的文件名
        if name == "AD":
            file_name = f"AD.txt"
            file_path = output_dir / file_name
        elif name == "AV":
            file_name = f"AV.txt"
            file_path = output_dir / file_name
        elif name == "AD_AV":
            file_name = f"AD_AV.txt"
            file_path = output_dir / file_name
        return file_path

class Modeler(Role):
    name: str = "Agent2"
    profile: str = "Modeler"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Modeling])

    async def _act(self):
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # todo will be SimpleWriteCode()
        msg = self.get_memories(k=1)[0]  # find the most recent messages
        json_dict = eval(msg.content)
        await todo.run(json_dict["ASR"], json_dict["FR"], json_dict["NFR"], json_dict["DC"])

async def main():
    #从config.json中读取需求文档
    with open("config.json", "r") as f:
        config = json.load(f)
    input_file = config["input_file"]
    file_name = os.path.basename(input_file).split(".")[0]
    output_root = Path("output//" + file_name.split(".")[0] + "//Modeler")
    Modeling.set_output_root(output_root)
    #从output文件夹中读取ASR,FR,NFR,DC
    path = ".\\output" + "\\" + file_name + "\\Analyst"
    with open(path+"\\ASR.txt") as f:
        ASR = f.read()
    with open(path + "\\FR.txt") as f:
        FR = f.read()
    with open(path + "\\NFR.txt") as f:
        NFR = f.read()
    with open(path + "\\DC.txt") as f:
        DC = f.read()
    #把这些信息放在一个json中
    json_mag = {"ASR":ASR, "FR":FR, "NFR":NFR, "DC":DC}
    #json转字符串
    json_str = str(json_mag)
    role = Modeler()
    result = await role.run(json_str)
    logger.info(result)

asyncio.run(main())