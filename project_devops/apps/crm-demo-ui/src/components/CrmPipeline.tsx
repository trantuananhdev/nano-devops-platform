import { KanbanSquare, Users, Phone, Calendar, DollarSign, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { VI } from "../lib/vi";

const PIPELINE_STAGES = [
  { id: 1, label: "Mới", desc: "Leads vừa được tạo" },
  { id: 2, label: "Đã liên hệ", desc: "Đã gọi điện" },
  { id: 3, label: "Đi xem", desc: "Có lịch hẹn xem" },
  { id: 4, label: "Đàm phán", desc: "Thương lượng giá" },
  { id: 5, label: "Thành công", desc: "Đã ký hợp đồng" },
];

export default function CrmPipeline() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-2">
        <KanbanSquare className="w-4 h-4 text-purple-600" />
        {VI.pipeline.title}
      </h2>
      <ol className="space-y-3">
        {PIPELINE_STAGES.map((stage) => (
          <li key={stage.id} className="flex gap-3 items-start">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-blue-500 text-xs font-bold text-white shadow-sm">
              {stage.id}
            </span>
            <div className="flex-1">
              <div className="font-medium text-slate-900">{stage.label}</div>
              <div className="text-xs text-slate-500">{stage.desc}</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
