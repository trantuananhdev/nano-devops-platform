"""Seed workflow BPMN diagrams — 3 quy trình dựa trên luồng thật EVN.

Idempotent: kiểm tra dossier_id trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import WorkflowDiagram

logger = logging.getLogger(__name__)

# BPMN XML cho quy trình thẩm định cơ bản 5 bước
BPMN_BASIC = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
             xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
             targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="basic_appraisal" name="Quy trình thẩm định cơ bản" isExecutable="false">
    <startEvent id="start" name="Nhận hồ sơ"/>
    <task id="task1" name="Kiểm tra đủ điều kiện"/>
    <task id="task2" name="AI Thẩm định"/>
    <task id="task3" name="Phê duyệt Trưởng phòng"/>
    <task id="task4" name="Phê duyệt HĐTV"/>
    <endEvent id="end" name="Hoàn tất"/>
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1"/>
    <sequenceFlow id="f2" sourceRef="task1" targetRef="task2"/>
    <sequenceFlow id="f3" sourceRef="task2" targetRef="task3"/>
    <sequenceFlow id="f4" sourceRef="task3" targetRef="task4"/>
    <sequenceFlow id="f5" sourceRef="task4" targetRef="end"/>
  </process>
  <bpmndi:BPMNDiagram id="diagram">
    <bpmndi:BPMNPlane id="plane" bpmnElement="basic_appraisal">
      <bpmndi:BPMNShape id="start_di" bpmnElement="start"><dc:Bounds x="152" y="82" width="36" height="36"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task1_di" bpmnElement="task1"><dc:Bounds x="240" y="60" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task2_di" bpmnElement="task2"><dc:Bounds x="410" y="60" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task3_di" bpmnElement="task3"><dc:Bounds x="580" y="60" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task4_di" bpmnElement="task4"><dc:Bounds x="750" y="60" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="end_di" bpmnElement="end"><dc:Bounds x="922" y="82" width="36" height="36"/></bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</definitions>"""

# BPMN XML cho quy trình có clarification 7 bước
BPMN_CLARIFICATION = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
             targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="clarification_flow" name="Quy trình thẩm định có yêu cầu làm rõ" isExecutable="false">
    <startEvent id="start" name="Nhận hồ sơ"/>
    <task id="task1" name="Kiểm tra đủ điều kiện"/>
    <task id="task2" name="AI Thẩm định sơ bộ"/>
    <userTask id="task3" name="Chuyên viên trả lời AI"/>
    <task id="task4" name="AI Hoàn thiện thẩm định"/>
    <task id="task5" name="Phê duyệt Trưởng phòng"/>
    <task id="task6" name="Phê duyệt HĐTV"/>
    <endEvent id="end" name="Hoàn tất"/>
    <intermediateCatchEvent id="clarif" name="AI Yêu cầu làm rõ"/>
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1"/>
    <sequenceFlow id="f2" sourceRef="task1" targetRef="task2"/>
    <sequenceFlow id="f3" sourceRef="task2" targetRef="clarif"/>
    <sequenceFlow id="f4" sourceRef="clarif" targetRef="task3"/>
    <sequenceFlow id="f5" sourceRef="task3" targetRef="task4"/>
    <sequenceFlow id="f6" sourceRef="task4" targetRef="task5"/>
    <sequenceFlow id="f7" sourceRef="task5" targetRef="task6"/>
    <sequenceFlow id="f8" sourceRef="task6" targetRef="end"/>
  </process>
  <bpmndi:BPMNDiagram id="diagram">
    <bpmndi:BPMNPlane id="plane" bpmnElement="clarification_flow">
      <bpmndi:BPMNShape id="start_di" bpmnElement="start"><dc:Bounds x="100" y="100" width="36" height="36"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task1_di" bpmnElement="task1"><dc:Bounds x="190" y="78" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task2_di" bpmnElement="task2"><dc:Bounds x="360" y="78" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="clarif_di" bpmnElement="clarif"><dc:Bounds x="530" y="100" width="36" height="36"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task3_di" bpmnElement="task3"><dc:Bounds x="620" y="78" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task4_di" bpmnElement="task4"><dc:Bounds x="790" y="78" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task5_di" bpmnElement="task5"><dc:Bounds x="960" y="78" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task6_di" bpmnElement="task6"><dc:Bounds x="1130" y="78" width="120" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="end_di" bpmnElement="end"><dc:Bounds x="1300" y="100" width="36" height="36"/></bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</definitions>"""

# BPMN XML cho quy trình phê duyệt HĐTV đầy đủ 9 bước (theo Mẫu KT thật)
BPMN_FULL_HDTV = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
             targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="hdtv_full" name="Quy trình phê duyệt HĐTV đầy đủ" isExecutable="false">
    <startEvent id="start" name="Phiếu trình B4"/>
    <task id="task1" name="PTGĐ xem xét sơ bộ"/>
    <task id="task2" name="Ban KT thẩm tra kỹ thuật"/>
    <task id="task3" name="Lập Báo cáo thẩm tra"/>
    <task id="task4" name="Lấy ý kiến tư vấn ngoài"/>
    <task id="task5" name="AI Tổng hợp ý kiến"/>
    <task id="task6" name="Trình Tổng Giám đốc"/>
    <task id="task7" name="HĐTV phê duyệt"/>
    <task id="task8" name="Ban hành Quyết định"/>
    <endEvent id="end" name="QĐ có hiệu lực"/>
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1"/>
    <sequenceFlow id="f2" sourceRef="task1" targetRef="task2"/>
    <sequenceFlow id="f3" sourceRef="task2" targetRef="task3"/>
    <sequenceFlow id="f4" sourceRef="task3" targetRef="task4"/>
    <sequenceFlow id="f5" sourceRef="task4" targetRef="task5"/>
    <sequenceFlow id="f6" sourceRef="task5" targetRef="task6"/>
    <sequenceFlow id="f7" sourceRef="task6" targetRef="task7"/>
    <sequenceFlow id="f8" sourceRef="task7" targetRef="task8"/>
    <sequenceFlow id="f9" sourceRef="task8" targetRef="end"/>
  </process>
  <bpmndi:BPMNDiagram id="diagram">
    <bpmndi:BPMNPlane id="plane" bpmnElement="hdtv_full">
      <bpmndi:BPMNShape id="start_di" bpmnElement="start"><dc:Bounds x="80" y="100" width="36" height="36"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task1_di" bpmnElement="task1"><dc:Bounds x="170" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task2_di" bpmnElement="task2"><dc:Bounds x="320" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task3_di" bpmnElement="task3"><dc:Bounds x="470" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task4_di" bpmnElement="task4"><dc:Bounds x="620" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task5_di" bpmnElement="task5"><dc:Bounds x="770" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task6_di" bpmnElement="task6"><dc:Bounds x="920" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task7_di" bpmnElement="task7"><dc:Bounds x="1070" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="task8_di" bpmnElement="task8"><dc:Bounds x="1220" y="78" width="100" height="80"/></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="end_di" bpmnElement="end"><dc:Bounds x="1370" y="100" width="36" height="36"/></bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</definitions>"""


WORKFLOW_DATA = [
    {"doc_no": "EVNHANOI-SCADA-2024-007", "bpmn_xml": BPMN_BASIC},
    {"doc_no": "EVNHANOI-UAV-198-2024", "bpmn_xml": BPMN_CLARIFICATION},
    {"doc_no": "EVNHANOI-MBA-2024-021", "bpmn_xml": BPMN_FULL_HDTV},
]


async def seed_workflow_diagrams(
    session: AsyncSession, dossier_id_map: dict[str, int]
) -> None:
    """Seed BPMN workflow diagrams."""
    for w in WORKFLOW_DATA:
        doc_no = w["doc_no"]
        dossier_id = dossier_id_map.get(doc_no)
        if not dossier_id:
            continue

        existing = (
            await session.execute(
                select(WorkflowDiagram).where(WorkflowDiagram.dossier_id == dossier_id)
            )
        ).scalar_one_or_none()

        if existing:
            logger.info("Workflow diagram already exists for: %s", doc_no)
            continue

        session.add(WorkflowDiagram(dossier_id=dossier_id, bpmn_xml=w["bpmn_xml"]))
        logger.info("Seeded workflow diagram for: %s", doc_no)

    await session.commit()
