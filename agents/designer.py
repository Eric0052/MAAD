from metagpt.actions import Action
from pathlib import Path
from metagpt.roles import Role
import asyncio
from metagpt.logs import logger
from metagpt.schema import Message
import json
import os

class Designinng(Action):
    PROMPT_TEMPLATE1: str = """"
    According to the provided requirements and architectural views, generate required UML diagrams using PlantUML syntax. \n
    Logical View contains Class Diagram, Object Diagram, State Diagram; \n
    Development View contains Package Diagram, Component Diagram; \n
    Process View contains Activity Diagram, Sequence Diagram, Collaboration Diagram; \n
    Physical View contains Deployment Diagram, Container Diagram; \n
    Scenario view contains Use Case Diagram \n
    Requirement: {verified_requirements}\n
    Architectural views: {AV}\n
    Structure your outputs as follows:
    1. Logical View:
    1.1 Class Diagram
    [PlantUML]
    1.2 Object Diagram
    [PlantUML]
    1.3 State Diagram
    [PlantUML]
    2. Development Views
    …
    """
    name: str = "Designinng"
    
    output_root : Path = Path("output//Designer")

    @classmethod
    def set_output_root(cls, output_root: Path):
        cls.output_root = output_root

    async def run(self, verified_requirements: str, AV: str):
        prompt1 = self.PROMPT_TEMPLATE1.format(verified_requirements=verified_requirements, AV=AV)
        rsp = await self._aask(prompt1)
        file_path = self.file_name()
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
    
    @classmethod
    def file_name(cls) -> str:
        output_dir = cls.output_root
        output_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"UML.txt"
        file_path = output_dir / file_name
        return file_path

class Desiner(Role):
    name: str = "Agent3"
    profile: str = "Designer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Designinng])

    async def _act(self):
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # todo will be SimpleWriteCode()
        msg = self.get_memories(k=1)[0]  # find the most recent messages
        json_dict = eval(msg.content)
        await todo.run(json_dict["verified_requirements"], json_dict["AV"])

async def main():
    with open("config.json", "r") as f:
        config = json.load(f)
    input_file = config["input_file"]
    file_name = os.path.basename(input_file).split(".")[0]
    output_root = Path("output//" + file_name.split(".")[0] + "//Designer")
    Designinng.set_output_root(output_root)
    with open(".\\output\\" + file_name.split(".")[0] + "\\Analyst\\VR.txt") as f:
        verified_requirements = f.read()
    with open(".\\output\\" + file_name.split(".")[0] + "\\Modeler\\AV.txt") as f:
        AV = f.read()
    json_dict = {"verified_requirements": verified_requirements, "AV": AV}
    json_str = str(json_dict)
    role = Desiner()
    result = await role.run(json_str)
    logger.info(result)

asyncio.run(main())