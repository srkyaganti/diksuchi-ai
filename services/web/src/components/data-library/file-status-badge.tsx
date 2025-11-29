import { Badge } from "@/components/ui/badge";

type FileStatus = "pending" | "processing" | "completed" | "failed";
type RagStatus = "none" | "processing" | "completed" | "failed";

interface FileStatusBadgeProps {
  status: FileStatus;
  ragStatus?: RagStatus;
}

export function FileStatusBadge({ status, ragStatus }: FileStatusBadgeProps) {
  // Show RAG status if it's not 'none'
  const displayStatus = ragStatus && ragStatus !== "none" ? ragStatus : status;

  const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    pending: "secondary",
    processing: "default",
    completed: "outline",
    failed: "destructive",
    none: "secondary",
  };

  const labels: Record<string, string> = {
    pending: "Pending",
    processing: "Processing",
    completed: "Completed",
    failed: "Failed",
    none: "Pending",
  };

  return (
    <Badge variant={variants[displayStatus] || "secondary"}>
      {labels[displayStatus] || displayStatus}
    </Badge>
  );
}
