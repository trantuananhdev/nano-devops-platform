"""Seed workflow BPMN diagrams — 3 quy trinh EVN HDTV thuc te.

Diagram 1: Quy trinh phe duyet HDTV 9 buoc — dua tren ho so 198/TTr-EVNHANOI that.
Diagram 2: Quy trinh AI tham dinh co clarification — flow chuan cho he thong.
Diagram 3: Quy trinh tham dinh co ban 5 buoc — cho ho so don gian.
Idempotent: kiem tra dossier_id truoc khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import WorkflowDiagram

logger = logging.getLogger(__name__)

BPMN_UAV_HDTV = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="evn_hdtv_uav" name="Quy trinh phe duyet HDTV 198/TTr-EVNHANOI" isExecutable="false">
    <startEvent id="start" name="Cong ty LDCT de xuat"/><task id="t1" name="Ban KT soan To trinh 07/KT (07/01/2025)"/><serviceTask id="t2" name="AI Tham dinh tu dong (LegalRAG + TCKT)"/><task id="t3" name="PTGD KT Nguyen Anh Dung ky phe duyet"/><task id="t4" name="TGD Nguyen Anh Tuan ky To trinh 198 (08/01/2025)"/><task id="t5" name="Ban Tong hop tham tra (24/01/2025)"/><task id="t6" name="Phieu trinh Chu tich HDTV (10/02/2025)"/><task id="t7" name="5 TV HDTV ky dong y (Do Tuan Anh, Nguyen Xuan Thang, Tran Van Thuong, Pham Dai Nghia, Ma Hoai Nam)"/><task id="t8" name="Chu tich HDTV Nguyen Danh Duyen ban hanh Nghi quyet"/>
    <endEvent id="end" name="Nghi quyet duoc ban hanh"/>
    <sequenceFlow id="f1" sourceRef="start" targetRef="t1"/><sequenceFlow id="f2" sourceRef="t1" targetRef="t2"/><sequenceFlow id="f3" sourceRef="t2" targetRef="t3"/><sequenceFlow id="f4" sourceRef="t3" targetRef="t4"/><sequenceFlow id="f5" sourceRef="t4" targetRef="t5"/><sequenceFlow id="f6" sourceRef="t5" targetRef="t6"/><sequenceFlow id="f7" sourceRef="t6" targetRef="t7"/><sequenceFlow id="f8" sourceRef="t7" targetRef="t8"/><sequenceFlow id="f9" sourceRef="t8" targetRef="end"/>
  </process>
  <bpmndi:BPMNDiagram id="diagram"><bpmndi:BPMNPlane id="plane" bpmnElement="evn_hdtv_uav">
    <bpmndi:BPMNShape id="s0" bpmnElement="start"><dc:Bounds x="80" y="122" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s1" bpmnElement="t1"><dc:Bounds x="170" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s2" bpmnElement="t2"><dc:Bounds x="350" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s3" bpmnElement="t3"><dc:Bounds x="530" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s4" bpmnElement="t4"><dc:Bounds x="710" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s5" bpmnElement="t5"><dc:Bounds x="890" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s6" bpmnElement="t6"><dc:Bounds x="1070" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s7" bpmnElement="t7"><dc:Bounds x="1250" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s8" bpmnElement="t8"><dc:Bounds x="1430" y="100" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s9" bpmnElement="end"><dc:Bounds x="1610" y="122" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNEdge id="e1" bpmnElement="f1"><di:waypoint x="116" y="140"/><di:waypoint x="170" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e2" bpmnElement="f2"><di:waypoint x="290" y="140"/><di:waypoint x="350" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e3" bpmnElement="f3"><di:waypoint x="470" y="140"/><di:waypoint x="530" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e4" bpmnElement="f4"><di:waypoint x="650" y="140"/><di:waypoint x="710" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e5" bpmnElement="f5"><di:waypoint x="830" y="140"/><di:waypoint x="890" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e6" bpmnElement="f6"><di:waypoint x="1010" y="140"/><di:waypoint x="1070" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e7" bpmnElement="f7"><di:waypoint x="1190" y="140"/><di:waypoint x="1250" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e8" bpmnElement="f8"><di:waypoint x="1370" y="140"/><di:waypoint x="1430" y="140"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e9" bpmnElement="f9"><di:waypoint x="1550" y="140"/><di:waypoint x="1610" y="140"/></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
</definitions>"""

BPMN_AI_CLARIFICATION = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="ai_clarification_flow" name="Quy trinh AI tham dinh co lam ro" isExecutable="false">
    <startEvent id="start" name="Nhan ho so"/><task id="t1" name="Kiem tra dieu kien ho so"/><serviceTask id="t2" name="AI Tham dinh (ReAct Agent)"/>
    <exclusiveGateway id="gw1" name="Can lam ro?"/>
    <userTask id="t3" name="Chuyen vien bo sung thong tin"/><task id="t4" name="Truong Ban xem xet ket qua AI"/><task id="t5" name="Phe duyet cap Ban"/><task id="t6" name="Trinh len HDTV"/>
    <endEvent id="end" name="Hoan tat"/>
    <sequenceFlow id="f1" sourceRef="start" targetRef="t1"/><sequenceFlow id="f2" sourceRef="t1" targetRef="t2"/><sequenceFlow id="f3" sourceRef="t2" targetRef="gw1"/>
    <sequenceFlow id="f4" name="Co" sourceRef="gw1" targetRef="t3"/><sequenceFlow id="f5" sourceRef="t3" targetRef="t2"/>
    <sequenceFlow id="f6" name="Khong" sourceRef="gw1" targetRef="t4"/><sequenceFlow id="f7" sourceRef="t4" targetRef="t5"/><sequenceFlow id="f8" sourceRef="t5" targetRef="t6"/><sequenceFlow id="f9" sourceRef="t6" targetRef="end"/>
  </process>
  <bpmndi:BPMNDiagram id="diagram"><bpmndi:BPMNPlane id="plane" bpmnElement="ai_clarification_flow">
    <bpmndi:BPMNShape id="s0" bpmnElement="start"><dc:Bounds x="80" y="152" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s1" bpmnElement="t1"><dc:Bounds x="170" y="130" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s2" bpmnElement="t2"><dc:Bounds x="350" y="130" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sg1" bpmnElement="gw1" isMarkerVisible="true"><dc:Bounds x="525" y="145" width="50" height="50"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s3" bpmnElement="t3"><dc:Bounds x="500" y="260" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s4" bpmnElement="t4"><dc:Bounds x="640" y="130" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s5" bpmnElement="t5"><dc:Bounds x="820" y="130" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s6" bpmnElement="t6"><dc:Bounds x="1000" y="130" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="se" bpmnElement="end"><dc:Bounds x="1180" y="152" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNEdge id="e1" bpmnElement="f1"><di:waypoint x="116" y="170"/><di:waypoint x="170" y="170"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e2" bpmnElement="f2"><di:waypoint x="290" y="170"/><di:waypoint x="350" y="170"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e3" bpmnElement="f3"><di:waypoint x="470" y="170"/><di:waypoint x="525" y="170"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e4" bpmnElement="f4"><di:waypoint x="550" y="195"/><di:waypoint x="550" y="260"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e5" bpmnElement="f5"><di:waypoint x="500" y="300"/><di:waypoint x="410" y="300"/><di:waypoint x="410" y="210"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e6" bpmnElement="f6"><di:waypoint x="575" y="170"/><di:waypoint x="640" y="170"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e7" bpmnElement="f7"><di:waypoint x="760" y="170"/><di:waypoint x="820" y="170"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e8" bpmnElement="f8"><di:waypoint x="940" y="170"/><di:waypoint x="1000" y="170"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e9" bpmnElement="f9"><di:waypoint x="1120" y="170"/><di:waypoint x="1180" y="170"/></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
</definitions>"""

BPMN_BASIC = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="basic_appraisal" name="Quy trinh tham dinh co ban" isExecutable="false">
    <startEvent id="start" name="Nhan ho so"/><task id="t1" name="Kiem tra dieu kien"/><serviceTask id="t2" name="AI Tham dinh"/><task id="t3" name="Phe duyet Truong ban"/><task id="t4" name="Phe duyet HDTV"/><endEvent id="end" name="Hoan tat"/>
    <sequenceFlow id="f1" sourceRef="start" targetRef="t1"/><sequenceFlow id="f2" sourceRef="t1" targetRef="t2"/><sequenceFlow id="f3" sourceRef="t2" targetRef="t3"/><sequenceFlow id="f4" sourceRef="t3" targetRef="t4"/><sequenceFlow id="f5" sourceRef="t4" targetRef="end"/>
  </process>
  <bpmndi:BPMNDiagram id="diagram"><bpmndi:BPMNPlane id="plane" bpmnElement="basic_appraisal">
    <bpmndi:BPMNShape id="s0" bpmnElement="start"><dc:Bounds x="152" y="82" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s1" bpmnElement="t1"><dc:Bounds x="240" y="60" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s2" bpmnElement="t2"><dc:Bounds x="410" y="60" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s3" bpmnElement="t3"><dc:Bounds x="580" y="60" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="s4" bpmnElement="t4"><dc:Bounds x="750" y="60" width="120" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="se" bpmnElement="end"><dc:Bounds x="922" y="82" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNEdge id="e1" bpmnElement="f1"><di:waypoint x="188" y="100"/><di:waypoint x="240" y="100"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e2" bpmnElement="f2"><di:waypoint x="360" y="100"/><di:waypoint x="410" y="100"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e3" bpmnElement="f3"><di:waypoint x="530" y="100"/><di:waypoint x="580" y="100"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e4" bpmnElement="f4"><di:waypoint x="700" y="100"/><di:waypoint x="750" y="100"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="e5" bpmnElement="f5"><di:waypoint x="870" y="100"/><di:waypoint x="922" y="100"/></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
</definitions>"""

WORKFLOWS_DATA = [
    {
        "doc_no": "198/TTr-EVNHANOI",
        "name": "Quy trinh phe duyet HDTV — 198/TTr-EVNHANOI",
        "description": (
            "9 buoc thuc te: Cong ty LDCT de xuat -> Ban KT soan 07/KT -> AI tham dinh -> "
            "PTGD KT Nguyen Anh Dung ky -> TGD Nguyen Anh Tuan ky To trinh 198 -> "
            "Ban Tong hop tham tra -> Phieu trinh HDTV -> 5 TV HDTV ky -> "
            "Chu tich HDTV Nguyen Danh Duyen ban hanh Nghi quyet"
        ),
        "bpmn_xml": BPMN_UAV_HDTV,
    },
    {
        "doc_no": "EVNHANOI-MBA-2024-021",
        "name": "Quy trinh AI tham dinh co lam ro",
        "description": (
            "Flow chuan: Nhan ho so -> Kiem tra dieu kien -> AI tham dinh (ReAct) -> "
            "Neu can lam ro: chuyen vien bo sung -> Truong ban xem xet -> Phe duyet Ban -> Trinh HDTV"
        ),
        "bpmn_xml": BPMN_AI_CLARIFICATION,
    },
    {
        "doc_no": "EVNHANOI-SCADA-2024-007",
        "name": "Quy trinh tham dinh co ban",
        "description": "5 buoc don gian cho ho so rui ro thap: Nhan ho so -> Kiem tra -> AI -> Truong ban -> HDTV",
        "bpmn_xml": BPMN_BASIC,
    },
]


async def seed_workflow_diagrams(
    session: AsyncSession, dossier_id_map: dict[str, int]
) -> None:
    for w in WORKFLOWS_DATA:
        doc_no = w["doc_no"]
        dossier_id = dossier_id_map.get(doc_no)

        existing = (
            await session.execute(
                select(WorkflowDiagram).where(WorkflowDiagram.dossier_id == dossier_id)
            )
        ).scalar_one_or_none()

        if existing:
            logger.info("WorkflowDiagram already exists for dossier: %s", doc_no)
            continue

        diagram = WorkflowDiagram(
            dossier_id=dossier_id,
            bpmn_xml=w["bpmn_xml"],
        )
        session.add(diagram)
        logger.info("Seeded workflow diagram: %s", w["name"])

    await session.commit()
