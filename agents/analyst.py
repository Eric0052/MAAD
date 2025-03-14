from metagpt.actions import Action
from pathlib import Path
from metagpt.roles import Role
import asyncio
from metagpt.logs import logger
from metagpt.schema import Message
import json
import os

class AnalyzeRequirement(Action):
    PROMPT_TEMPLATE_ANALYZE: str = """
    Given the following requirement documents, analyze and resolve any conflicts or redundancies between the requirements. 
    Integrate them into a coherent and consistent set of requirements. 
    The output should be a structured requirements document, formatted as one requirement per line, with conflicts addressed and redundancies removed: {requirement_documents}
    """

    PROMPT_TEMPLATE_VERIFY: str = """
    Please verify the following requirements and ensure they are consistent, complete, and accurate with the original requirements:\n
    - Requirements need to be verified: {processed_requirements}
    - Original requirements: {requirement_documents}
    Perform the following tasks:
    1.Verify that each requirement is consistent and free of contradictions.
    2.Detect any redundant or conflicting entries.
    3.Create an output file named "verified_requirements.txt" that lists only the approved, non-conflicting requirements.
    Additionally, supply a summary of any conflicts, contradictions, or redundancies that were resolved.
    """

    #生成ASR
    PROMPT_TEMPLATE1: str = """"
    Given the software requirements below\n
    {verified_requirements}\n
    Generate Architecturally Significant Requirements (ASRs) from the provided requirements. For each ASR, the criteria are: influence system architectural decisions, involves critical quality attributes, require cross-component coordination. 
    Structure your outputs as follows:\n
    "The ASRs are:\n
    1. [ASR-001]:\n
    - [Original text of ASR1]\n
    - [Related quality attribute(s)]\n
    - [Architectural Impact]\n
    2. [ASR-002]:
    ..."

    An example is here:
    1. ASR-001
    - Original text of ASR1: The system must support 100,000 concurrent requests per second
    - [Related quality attribute(s)]: Scalability, Availability, Performance efficiency, Fault Tolerance
    - Architectural Impact: Distributed architecture design is required
    - Related Components: API Gateway, Load Balancer
    ...
    """

    #生成FR
    PROMPT_TEMPLATE2: str = """
    Here is a provided software requirements \n
    {verified_requirements}\n
    Provide a concise summary of the functional requirements (FR). Specifically, identify the features and tasks outlined in the document. Structure your outputs as follows:\n
    "The functional requirements are:\n
    1. [FR-001]  
    1.1 [Task 1 ]
    1.2 [Task 2]
    …
    2. [FR-002]
    2.1 [Task 1]
    ..."
    """

    #生成non-functional requirements
    PROMPT_TEMPLATE3: str = """
    Here is a provided software requirements specification\n
    {verified_requirements}\n  
    Based on the provided software requirements specification, please summarize all Non-functional Requirements (NFR). Structure your outputs as follows:\n
    "The Non-functional Requirements are:\n
    1. [NFR-001]:\n
    - [Original text of NFR-001]\n
    - [Related quality attribute(s)]\n
    2. [NFR-002]:
    ..."
    """

    PROMPT_TEMPLATE4: str = """"
    Here is a provided software requirements specification\n
    {verified_requirements}\n  
    Based on the provided software requirements specification, please generate the Design Constraints (DC). Structure your outputs as follows:\n
    "The Design Constraints are:\n
    1. DC-001: XXXX
    2. DC-002: XXXX
    ..."
    """
    name: str = "AnalyzeRequirement"
    
    requirement_root : Path = Path("output//Analyst")

    #根据json文件中的配置信息，生成对应的文件名
    @classmethod
    def set_output_root(cls, requirement_root: Path):
        cls.requirement_root = requirement_root

    async def run(self, requirement_documents: str):
        prompt_analyze = self.PROMPT_TEMPLATE_ANALYZE.format(requirement_documents=requirement_documents)
        integrated_requirements = await self._aask(prompt_analyze)
        file_path = self.file_name("IntegratedRequirements")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(integrated_requirements)
        prompt_verify = self.PROMPT_TEMPLATE_VERIFY.format(processed_requirements=integrated_requirements, requirement_documents=requirement_documents)
        verified_requirements = await self._aask(prompt_verify)
        file_path = self.file_name("VerifiedRequirements")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(verified_requirements)
        prompt1 = self.PROMPT_TEMPLATE1.format(verified_requirements=verified_requirements)
        rsp = await self._aask(prompt1)
        file_path = self.file_name("ASR")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
        prompt2 = self.PROMPT_TEMPLATE2.format(verified_requirements=verified_requirements)
        rsp = await self._aask(prompt2)
        file_path = self.file_name("FR")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
        prompt3 = self.PROMPT_TEMPLATE3.format(verified_requirements=verified_requirements)
        rsp = await self._aask(prompt3)
        file_path = self.file_name("NFR")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
        prompt4 = self.PROMPT_TEMPLATE4.format(verified_requirements=verified_requirements)
        rsp = await self._aask(prompt4)
        file_path = self.file_name("DC")
        with file_path.open("w") as f:
            f.write(rsp)

    @classmethod
    def file_name(cls, name : str) -> str:
        output_dir = cls.requirement_root
        output_dir.mkdir(parents=True, exist_ok=True)
        # 查找现有文件并生成新的文件名
        if name == "IntegratedRequirements":
            file_name = f"IntegratedRequirements.txt"
            file_path = output_dir / file_name
        elif name == "VerifiedRequirements":
            file_name = f"VerifiedRequirements.txt"
            file_path = output_dir / file_name
        elif name == "ASR":
            file_name = f"ASR.txt"
            file_path = output_dir / file_name
        elif name == "FR":
            file_name = f"FR.txt"
            file_path = output_dir / file_name
        elif name == "NFR":
            file_name = f"NFR.txt"
            file_path = output_dir / file_name
        elif name == "DC":
            file_name = f"DC.txt"
            file_path = output_dir / file_name
        return file_path

class Analyst(Role):
    name: str = "Agent1"
    profile: str = "Analyst"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AnalyzeRequirement])

    async def _act(self):
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # todo will be SimpleWriteCode()

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        await todo.run(msg.content)

async def main():
    #从config.json中读取需求文档
    with open("config.json", "r") as f:
        config = json.load(f)
    input_file = config["input_file"]
    #读取需求文档
    with open(input_file, "r", encoding='utf-8') as f:
        requirement = f.read()
    role = Analyst()
    file_name = os.path.basename(input_file)
    # print(input_file)
    #根据读取的input_file修改requirement_root
    requirement_root = Path("output//" + file_name.split(".")[0] + "//Analyst")
    AnalyzeRequirement.set_output_root(requirement_root)
    result = await role.run(requirement)
    logger.info(result)

asyncio.run(main())