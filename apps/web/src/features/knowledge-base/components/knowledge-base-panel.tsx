"use client";

import { Alert, Card, CardBody, CardHeader, Skeleton } from "@/shared/ui";
import { useDocuments } from "../hooks";
import { DocumentTable } from "./document-table";
import { LimitsMeter } from "./limits-meter";
import { UploadPanel } from "./upload-panel";

export function KnowledgeBasePanel() {
  const { data, isLoading, error } = useDocuments();
  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (error || !data) return <Alert>{error?.message ?? "Couldn't load documents."}</Alert>;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <Card className="order-2 overflow-hidden lg:order-1">
        <CardHeader title="All documents" description={`${data.documents.length} uploaded`} />
        <div className="mt-5 border-t border-border">
          <DocumentTable documents={data.documents} />
        </div>
      </Card>
      <Card className="order-1 h-fit lg:order-2">
        <CardHeader title="Upload" />
        <CardBody className="space-y-6">
          <LimitsMeter limits={data.limits} />
          <UploadPanel limits={data.limits} />
        </CardBody>
      </Card>
    </div>
  );
}
