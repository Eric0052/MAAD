from metagpt.actions import Action
from pathlib import Path
from metagpt.roles import Role
import asyncio
from metagpt.logs import logger
from metagpt.schema import Message
import re
import json
import os

class Evaluating(Action):
    #生成Mismatch report
    PROMPT_TEMPLATE1: str = """"
    According to the provided requirements and UML diagrams (recorded in PlantUML syntax), please generate a Mismatch Analysis Report. \n
    1. Requirement: {verified_requirements}\n
    2. UML views: {UML}\n
    Your report should identify any discrepancies, inconsistencies, or gaps between the system requirements and the architectural design. Structure your outputs as follows:\n
    [mismatch 1]
    - Description: A brief explanation of the mismatch.
    - Impact: An analysis of the potential impact on the system.
    - Recommendation: Suggestions or steps to resolve or mitigate the issue.
    [mismatch 2]
    - Description: A brief explanation of the mismatch.
    - Impact: An analysis of the potential impact on the system.
    - Recommendation: Suggestions or steps to resolve or mitigate the issue
    ……
    """

    #生成ATAM
    PROMPT_TEMPLATE2: str = """
    According to the provided requirements and UML diagrams, please generate an architecture evaluation report based on the ATAM method.\n
    1. Requirement: {verified_requirements}\n
    2. UML views: {UML}\n
    Your report should include the following content:
    1. A concise presentation of the architecture: an architectural presentation that is both concise and, usually, understandable.
    2. Articulation of the business goals: the business goals presented in the ATAM exercise are being seen by some of the assembled participants for the first time and these are captured in the outputs.
    3. Prioritized quality attribute requirements expressed as quality attribute scenarios: uses prioritized quality attribute scenarios as the basis for evaluating the architecture.
    4. A set of risks and non-risks: An architectural risk is a decision that may lead to undesirable consequences in light of stated quality attribute requirements. Similarly, an architectural non-risk is a decision that, upon analysis, is deemed safe.
    5. A set of risk themes: When the analysis is complete, the evaluation team examines the full set of discovered risks to look for overarching themes that identify systemic weaknesses in the architecture or even in the architecture process and team. If left untreated, these risk themes will threaten the project’s business goals.
    6. Mapping of architectural decisions to quality requirements: Architectural decisions can be interpreted in terms of the drivers that they support or hinder.
    7. A set of identified sensitivity points and tradeoff points: Sensitivity points are architectural decisions that have a marked effect on a quality attribute response. Tradeoffs occur when two or more quality attribute responses are sensitive to the same architectural decision, but one of them improves while the other degrades—hence the tradeoff.
    """

    #生成Refinement suggestions
    PROMPT_TEMPLATE3: str = """
    According to the provided requirements and UML views, please generate a list of refinement suggestions aimed at enhancing the system design. Your suggestions should identify areas for improvement or optimization and provide actionable recommendations. \n
    Requirement: {verified_requirements}\n
    Architectural views: {AV}\n
    Structure your outputs as follows:
    Suggestion 1:
    - Issue/Opportunity: [Description]
    - Proposed Refinement: [Detail the refinement]
    - Rationale/Benefit: [Explain the benefit]
    Suggestion 2:
    ……
    """
    name: str = "Evaluating"
    output_root : Path = Path("output//Designer")

    @classmethod
    def set_output_root(cls, output_root: Path):
        cls.output_root = output_root    
    
    async def run(self, verified_requirements: str, AV: str, UML: str):
        prompt1 = self.PROMPT_TEMPLATE1.format(verified_requirements=verified_requirements, UML=UML)    
        rsp = await self._aask(prompt1)
        #计算mismatch的数量
        mismatch_count = self.count_mismatch(rsp)
        #计算requirement的数量
        requirement_count = self.count_requirement()
        #计算mismatch的比例
        mismatch_rate = mismatch_count/requirement_count
        file_path = self.file_name("MAR")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
            #继续写入mismatch的数量和比例
            f.write(f"\nMismatch count: {mismatch_count}")
            f.write(f"\nRequirement count: {requirement_count}")
            f.write(f"\nMismatch rate: {mismatch_rate}")
        prompt2 = self.PROMPT_TEMPLATE2.format(verified_requirements=verified_requirements, UML=UML)  
        rsp = await self._aask(prompt2)
        file_path = self.file_name("ATAM")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
        prompt3 = self.PROMPT_TEMPLATE3.format(verified_requirements=verified_requirements, AV=AV)  
        rsp = await self._aask(prompt3)
        file_path = self.file_name("RS")
        with file_path.open("w", encoding="utf-8") as f:
            f.write(rsp)
    
    @classmethod
    def file_name(cls, name : str) -> str:
        output_dir = cls.output_root
        output_dir.mkdir(parents=True, exist_ok=True)
        # 查找现有文件并生成新的文件名
        if name == "MAR":
            file_name = f"MAR.txt"
            file_path = output_dir / file_name
        elif name == "ATAM":
            file_name = f"ATAM.txt"
            file_path = output_dir / file_name
        elif name == "RS":
            file_name = f"RS.txt"
            file_path = output_dir / file_name
        return file_path

    #读取VR_1.txt中requirement的数量
    @classmethod
    def count_requirement(cls):
        file_name = os.path.normpath(cls.output_root).split(os.sep)[1]
        with open("C:\\Research\\MAAD\\demo\\demo_v2\\output\\" + file_name + "\\Analyst\\VR.txt") as f:
            content = f.read()
        requirements = re.findall(r'^\d+\.', content, re.MULTILINE)
        return len(requirements)
    #读取MAR_1.txt中mismatch的数量
    @staticmethod
    def count_mismatch(rsp):
        mismatches = re.findall(r'Mismatch \d+', rsp)
        return len(mismatches)

class Evaluator(Role):
    name: str = "Agent4"
    profile: str = "Evaluator"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Evaluating])

    async def _act(self):
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # todo will be SimpleWriteCode()
        msg = self.get_memories(k=1)[0]  # find the most recent messages
        # #打印msg类型
        # logger.info(msg)
        #json字符串转dict
        json_dict = eval(msg.content)
        await todo.run(json_dict["requirement"], json_dict["AV"], json_dict["UML"])

async def main():
    with open("config.json", "r") as f:
        config = json.load(f)
    input_file = config["input_file"]
    file_name = os.path.basename(input_file).split(".")[0]
    output_root = Path("output//" + file_name.split(".")[0] + "//Evaluator")
    Evaluating.set_output_root(output_root)
    #从output文件夹中读取ASR,FR,NFR,DCPR
    #读取需求文档
    with open(input_file, "r", encoding='utf-8') as f:
        requirement = f.read()
    with open(".\\output\\" + file_name.split(".")[0] + "\\Modeler\\AV.txt") as f:
        AV = f.read()
    with open(".\\output\\" + file_name.split(".")[0] + "\\Designer\\UML.txt") as f:
        UML = f.read()
    #把这些信息放在一个json中
    json_msg = {"requirement":requirement, "AV":AV, "UML":UML}
    #json转字符串
    json_str = str(json_msg)
    role = Evaluator()
    result = await role.run(json_str)
    logger.info(result)

asyncio.run(main())